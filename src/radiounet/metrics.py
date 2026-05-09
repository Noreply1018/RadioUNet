from __future__ import annotations

import math
from dataclasses import dataclass

import torch
import torch.nn as nn


_MSE = nn.MSELoss()


@dataclass
class OutputMetrics:
    mse: float
    nmse: float
    rmse: float
    rmse_db_80: float


def mse(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    return _MSE(pred, target)


def nmse(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    denominator = _MSE(target, torch.zeros_like(target))
    if denominator.item() == 0:
        raise ZeroDivisionError("Cannot compute NMSE because target energy is zero.")
    return _MSE(pred, target) / denominator


def sparse_mse(
    pred: torch.Tensor,
    target: torch.Tensor,
    samples: torch.Tensor,
    num_samples_for_loss: int | None = None,
) -> torch.Tensor:
    mask = samples.to(dtype=pred.dtype)
    if mask.shape != pred.shape:
        raise ValueError(f"Sparse mask shape {tuple(mask.shape)} does not match prediction shape {tuple(pred.shape)}.")
    denominator = float(num_samples_for_loss) if num_samples_for_loss is not None else float(mask.sum().detach().cpu())
    if denominator <= 0:
        raise ValueError("Sparse MSE requires at least one masked measurement point.")
    squared_error = ((pred - target) ** 2) * mask
    batch_size = max(int(pred.shape[0]), 1)
    return squared_error.sum() / (batch_size * denominator)


def summarize(pred: torch.Tensor, target: torch.Tensor) -> OutputMetrics:
    mse_value = float(mse(pred, target).detach().cpu())
    nmse_value = float(nmse(pred, target).detach().cpu())
    rmse_value = math.sqrt(mse_value)
    return OutputMetrics(
        mse=mse_value,
        nmse=nmse_value,
        rmse=rmse_value,
        rmse_db_80=rmse_value * 80,
    )


def accumulate_dense(pred1: torch.Tensor, pred2: torch.Tensor, target: torch.Tensor, batch_size: int) -> dict[str, float]:
    first = summarize(pred1, target)
    second = summarize(pred2, target)
    return {
        "firstU_mse": first.mse * batch_size,
        "firstU_nmse": first.nmse * batch_size,
        "firstU_rmse": first.rmse * batch_size,
        "firstU_rmse_db_80": first.rmse_db_80 * batch_size,
        "secondU_mse": second.mse * batch_size,
        "secondU_nmse": second.nmse * batch_size,
        "secondU_rmse": second.rmse * batch_size,
        "secondU_rmse_db_80": second.rmse_db_80 * batch_size,
    }
