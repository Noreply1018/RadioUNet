from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

import numpy as np
import torch
from scipy.interpolate import RBFInterpolator, griddata
from scipy.ndimage import binary_dilation


@dataclass(frozen=True)
class BaselineResult:
    prediction: np.ndarray
    seconds: float
    used_building_postprocessing: bool
    per_map_optimized: bool
    implementation: str


def tensor_to_hw(value: torch.Tensor | np.ndarray) -> np.ndarray:
    if isinstance(value, torch.Tensor):
        array = value.detach().cpu().numpy()
    else:
        array = np.asarray(value)
    array = np.squeeze(array)
    if array.ndim != 2:
        raise ValueError(f"Expected a 2D image after squeeze, got shape {array.shape}.")
    return array.astype(np.float32, copy=False)


def sparse_points(samples: torch.Tensor | np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    image = tensor_to_hw(samples)
    coords = np.argwhere(image != 0)
    values = image[coords[:, 0], coords[:, 1]] if coords.size else np.asarray([], dtype=np.float32)
    return coords.astype(np.float32), values.astype(np.float32)


def _grid(shape: tuple[int, int]) -> np.ndarray:
    rows, cols = np.indices(shape, dtype=np.float32)
    return np.column_stack([rows.ravel(), cols.ravel()])


def _fill_empty(shape: tuple[int, int], value: float = 0.0) -> np.ndarray:
    return np.full(shape, value, dtype=np.float32)


def _clip_like_target(prediction: np.ndarray) -> np.ndarray:
    return np.clip(np.nan_to_num(prediction, nan=0.0, posinf=256.0, neginf=0.0), 0.0, 256.0).astype(np.float32)


def rbf_interpolation(samples: torch.Tensor | np.ndarray, *, smoothing: float = 10.0, neighbors: int = 50) -> BaselineResult:
    start = time.time()
    sample_image = tensor_to_hw(samples)
    coords, values = sparse_points(sample_image)
    if len(values) == 0:
        prediction = _fill_empty(sample_image.shape)
    elif len(values) < 4:
        prediction = _fill_empty(sample_image.shape, float(values.mean()))
    else:
        interpolator = RBFInterpolator(
            coords,
            values,
            kernel="thin_plate_spline",
            smoothing=smoothing,
            neighbors=min(neighbors, len(values)),
        )
        prediction = interpolator(_grid(sample_image.shape)).reshape(sample_image.shape)
    return BaselineResult(
        prediction=_clip_like_target(prediction),
        seconds=time.time() - start,
        used_building_postprocessing=False,
        per_map_optimized=True,
        implementation=f"scipy RBFInterpolator(thin_plate_spline, neighbors={min(neighbors, max(len(values), 1))})",
    )


def tensor_completion_proxy(samples: torch.Tensor | np.ndarray) -> BaselineResult:
    start = time.time()
    sample_image = tensor_to_hw(samples)
    coords, values = sparse_points(sample_image)
    if len(values) == 0:
        prediction = _fill_empty(sample_image.shape)
    else:
        grid = _grid(sample_image.shape)
        prediction = griddata(coords, values, grid, method="linear", fill_value=np.nan).reshape(sample_image.shape)
        if np.isnan(prediction).any():
            nearest = griddata(coords, values, grid, method="nearest").reshape(sample_image.shape)
            prediction = np.where(np.isnan(prediction), nearest, prediction)
    return BaselineResult(
        prediction=_clip_like_target(prediction),
        seconds=time.time() - start,
        used_building_postprocessing=False,
        per_map_optimized=True,
        implementation="scipy griddata linear+nearest proxy for tensor completion",
    )


def tomography_proxy(samples: torch.Tensor | np.ndarray, tx: torch.Tensor | np.ndarray, buildings: torch.Tensor | np.ndarray) -> BaselineResult:
    start = time.time()
    sample_image = tensor_to_hw(samples)
    tx_image = tensor_to_hw(tx)
    building_image = tensor_to_hw(buildings)
    coords, values = sparse_points(sample_image)
    if len(values) == 0:
        prediction = _fill_empty(sample_image.shape)
    else:
        grid = _grid(sample_image.shape)
        tx_coords = np.argwhere(tx_image == tx_image.max())
        tx_coord = tx_coords.mean(axis=0) if len(tx_coords) else np.asarray(sample_image.shape, dtype=np.float32) / 2.0
        sample_dist = np.linalg.norm(coords - tx_coord, axis=1)
        grid_dist = np.linalg.norm(grid - tx_coord, axis=1)
        if float(np.std(sample_dist)) > 1e-6:
            slope, intercept = np.polyfit(sample_dist, values, deg=1)
            prediction = (slope * grid_dist + intercept).reshape(sample_image.shape)
        else:
            prediction = _fill_empty(sample_image.shape, float(values.mean()))
        obstacle = binary_dilation(building_image > 0.1, iterations=1)
        prediction = prediction - obstacle.astype(np.float32) * 8.0
    return BaselineResult(
        prediction=_clip_like_target(prediction),
        seconds=time.time() - start,
        used_building_postprocessing=True,
        per_map_optimized=True,
        implementation="distance-to-Tx regression with building attenuation proxy for tomography",
    )


def one_step_mlp_proxy(samples: torch.Tensor | np.ndarray, tx: torch.Tensor | np.ndarray, buildings: torch.Tensor | np.ndarray) -> BaselineResult:
    start = time.time()
    sample_image = tensor_to_hw(samples)
    tx_image = tensor_to_hw(tx)
    building_image = tensor_to_hw(buildings)
    coords, values = sparse_points(sample_image)
    if len(values) < 3:
        prediction = _fill_empty(sample_image.shape, float(values.mean()) if len(values) else 0.0)
    else:
        rows, cols = np.indices(sample_image.shape, dtype=np.float32)
        tx_coords = np.argwhere(tx_image == tx_image.max())
        tx_coord = tx_coords.mean(axis=0) if len(tx_coords) else np.asarray(sample_image.shape, dtype=np.float32) / 2.0
        dist = np.linalg.norm(np.column_stack([rows.ravel(), cols.ravel()]) - tx_coord, axis=1).reshape(sample_image.shape)
        features = np.column_stack(
            [
                np.ones(len(coords), dtype=np.float32),
                coords[:, 0] / sample_image.shape[0],
                coords[:, 1] / sample_image.shape[1],
                np.linalg.norm(coords - tx_coord, axis=1) / max(sample_image.shape),
                building_image[coords[:, 0].astype(int), coords[:, 1].astype(int)],
            ]
        )
        weights, *_ = np.linalg.lstsq(features, values, rcond=None)
        full_features = np.stack(
            [
                np.ones_like(rows),
                rows / sample_image.shape[0],
                cols / sample_image.shape[1],
                dist / max(sample_image.shape),
                building_image,
            ],
            axis=-1,
        )
        prediction = np.tensordot(full_features, weights, axes=([-1], [0]))
    return BaselineResult(
        prediction=_clip_like_target(prediction),
        seconds=time.time() - start,
        used_building_postprocessing=False,
        per_map_optimized=True,
        implementation="per-map linear least-squares proxy for one-step MLP",
    )


BASELINES: dict[str, Callable[..., BaselineResult]] = {
    "rbf": rbf_interpolation,
    "tensor_completion": tensor_completion_proxy,
    "tomography": tomography_proxy,
    "one_step_mlp": one_step_mlp_proxy,
}
