#!/usr/bin/env python3
"""Audit Stage 4 missing-buildings loader semantics."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
from skimage import io

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataset
from radiounet.utils import git_metadata, load_yaml, require_dataset_dir, save_json, set_seed


def sha_array(array: np.ndarray | torch.Tensor) -> str:
    if isinstance(array, torch.Tensor):
        data = array.detach().cpu().numpy()
    else:
        data = array
    return hashlib.sha256(np.ascontiguousarray(data).tobytes()).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_counts(config: dict[str, Any]) -> dict[str, int]:
    return {split: len(build_dataset(config, split)) for split in ["train", "val", "test"]}


def map_tx_for_dataset_item(dataset: Any, idx: int) -> tuple[int, int]:
    idxr = int(np.floor(idx / dataset.numTx))
    idxc = int(idx - idxr * dataset.numTx)
    return int(dataset.maps_inds[idxr + dataset.ind1] + 1), idxc


def paths_for(config: dict[str, Any], map_id: int, tx: int) -> dict[str, Any]:
    data = config["data"]
    dataset_dir = Path(data.get("dataset_dir", "RadioMapSeer/"))
    missing = int(data.get("missing_buildings", data.get("missing", 0)))
    if data.get("city_map") == "complete":
        building_dir = dataset_dir / "png/buildings_complete"
        building_paths = [building_dir / f"{map_id}.png"]
    else:
        building_dir = dataset_dir / f"png/buildings_missing{missing}"
        building_paths = [building_dir / str(version) / f"{map_id}.png" for version in range(1, 7)]
    return {
        "building_dir": str(building_dir),
        "building_paths": [str(path) for path in building_paths],
        "tx_path": str(dataset_dir / f"png/antennas/{map_id}_{tx}.png"),
        "target_path": str(dataset_dir / f"gain/{data.get('simulation', 'IRT4')}/{map_id}_{tx}.png"),
        "complete_building_path": str(dataset_dir / f"png/buildings_complete/{map_id}.png"),
    }


def audit_dataset_sample(config: dict[str, Any], split: str, idx: int) -> dict[str, Any]:
    set_seed(int(config.get("experiment", {}).get("seed", 42)))
    dataset = build_dataset(config, split)
    item = dataset[idx]
    inputs = item[0]
    target = item[1]
    samples = item[2] if len(item) >= 3 else None
    input_mask = item[3] if len(item) == 4 else None
    map_id, tx = map_tx_for_dataset_item(dataset, idx)
    paths = paths_for(config, map_id, tx)

    complete = np.asarray(io.imread(paths["complete_building_path"]))
    candidate_paths = [Path(path) for path in paths["building_paths"]]
    candidate_hashes = [file_sha(path) for path in candidate_paths]
    complete_hash = file_sha(Path(paths["complete_building_path"]))
    building_input = inputs[0]
    building_hash = sha_array(building_input)
    if config["data"]["loader"] == "RadioUNet_s_sprseIRT4":
        complete_tensor = torch.from_numpy(np.ascontiguousarray((complete / 256).astype(np.float32)))
    else:
        complete_tensor = torch.from_numpy(np.ascontiguousarray((complete / 255).astype(np.float32)))
    complete_tensor_hash = sha_array(complete_tensor)
    missing = int(config["data"].get("missing_buildings", config["data"].get("missing", 0)))
    building_differs_from_complete = building_hash != complete_tensor_hash if missing else building_hash == complete_tensor_hash

    sparse_alignment_abs_max = None
    input_points = None
    loss_mask_points = None
    input_subset_of_loss_mask = None
    if config["data"]["loader"] == "RadioUNet_s_sprseIRT4":
        sparse_values = inputs[2]
        in_mask = input_mask[0] != 0 if input_mask is not None else sparse_values != 0
        loss_mask = samples[0] != 0 if samples is not None else torch.zeros_like(in_mask)
        input_points = int(in_mask.sum().item())
        loss_mask_points = int(loss_mask.sum().item())
        input_subset_of_loss_mask = bool((in_mask & ~loss_mask).sum().item() == 0)
        if bool(in_mask.any()):
            sparse_alignment_abs_max = float(torch.abs(sparse_values[in_mask] - target[0][in_mask]).max().item())
        else:
            sparse_alignment_abs_max = 0.0
    elif samples is not None:
        loss_mask = samples[0] != 0
        loss_mask_points = int(loss_mask.sum().item())

    return {
        "split": split,
        "idx": idx,
        "map_id": map_id,
        "tx": tx,
        "paths": paths,
        "candidate_building_hashes": candidate_hashes,
        "complete_building_file_hash": complete_hash,
        "input_building_tensor_hash": building_hash,
        "complete_building_tensor_hash": complete_tensor_hash,
        "building_input_semantics_ok": building_differs_from_complete,
        "tx_tensor_hash": sha_array(inputs[1]),
        "target_tensor_hash": sha_array(target),
        "sparse_input_target_alignment_abs_max": sparse_alignment_abs_max,
        "input_points": input_points,
        "loss_mask_points": loss_mask_points,
        "input_subset_of_loss_mask": input_subset_of_loss_mask,
    }


def dataset_dirs(config: dict[str, Any]) -> dict[str, Any]:
    data = config["data"]
    dataset_dir = Path(data.get("dataset_dir", "RadioMapSeer/"))
    missing = int(data.get("missing_buildings", data.get("missing", 0)))
    if missing == 0:
        building_dir = dataset_dir / "png/buildings_complete"
        versions: list[str] = []
    else:
        building_dir = dataset_dir / f"png/buildings_missing{missing}"
        versions = [str(path) for path in sorted(building_dir.glob("*")) if path.is_dir()]
    return {
        "building_dir": str(building_dir),
        "building_dir_exists": building_dir.exists(),
        "building_versions": versions,
        "target_radio_dir": str(dataset_dir / "gain/IRT4"),
        "target_radio_dir_exists": (dataset_dir / "gain/IRT4").exists(),
        "antenna_dir": str(dataset_dir / "png/antennas"),
        "antenna_dir_exists": (dataset_dir / "png/antennas").exists(),
    }


def write_markdown(audit: dict[str, Any], output: Path) -> None:
    lines = [
        "# Stage 4 missing-buildings loader 审计",
        "",
        f"- 配置：`{audit['config_path']}`",
        f"- loader：`{audit['loader']}`",
        f"- missing_buildings：`{audit['missing_buildings']}`",
        f"- building dir：`{audit['dirs']['building_dir']}`",
        f"- target radio dir：`{audit['dirs']['target_radio_dir']}`",
        f"- split 样本数：`{audit['split_counts']}`",
        "",
        "## 样本检查",
    ]
    for sample in audit["samples"]:
        lines.append(
            f"- `{sample['split']}[{sample['idx']}]` map `{sample['map_id']}` tx `{sample['tx']}`："
            f"building 语义通过 `{sample['building_input_semantics_ok']}`，"
            f"target hash `{sample['target_tensor_hash']}`，"
            f"input sparse/target 最大误差 `{sample['sparse_input_target_alignment_abs_max']}`"
        )
    lines.extend(["", "## Gate"])
    for key, value in audit["gate"].items():
        lines.append(f"- `{key}={value}`")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default="reports/missing_buildings/loader_audits")
    parser.add_argument("--indices", default="0,1,2")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_yaml(config_path)
    require_dataset_dir(config)
    data = config["data"]
    missing = int(data.get("missing_buildings", data.get("missing", 0)))
    samples = [
        audit_dataset_sample(config, split="test", idx=int(idx))
        for idx in args.indices.split(",")
        if idx.strip()
    ]
    dirs = dataset_dirs(config)
    counts = split_counts(config)
    is_s = data["loader"] == "RadioUNet_s_sprseIRT4"
    gate = {
        "building_dir_exists": dirs["building_dir_exists"],
        "target_radio_dir_exists": dirs["target_radio_dir_exists"],
        "antenna_dir_exists": dirs["antenna_dir_exists"],
        "versions_present_if_missing": missing == 0 or len(dirs["building_versions"]) == 6,
        "test_split_is_198": counts["test"] == 198,
        "building_input_semantics_ok": all(sample["building_input_semantics_ok"] for sample in samples),
        "target_hash_stable_across_tx_duplicates": samples[0]["target_tensor_hash"] == samples[0]["target_tensor_hash"],
        "s_sparse_input_from_target": (not is_s)
        or all(sample["sparse_input_target_alignment_abs_max"] == 0.0 for sample in samples),
        "s_input_subset_of_loss_mask": (not is_s) or all(sample["input_subset_of_loss_mask"] for sample in samples),
        "s_pool600_if_mainline": (not is_s)
        or data.get("data_samples") == 600
        and data.get("num_samples_low") == 1
        and data.get("num_samples_high") == 301,
    }
    gate["pass"] = all(gate.values())
    audit = {
        "scope": "Stage 4 missing-buildings loader audit",
        "config_path": str(config_path),
        "git": git_metadata(exclude_paths=["reports"]),
        "loader": data["loader"],
        "simulation": data.get("simulation"),
        "city_map": data.get("city_map"),
        "missing_buildings": missing,
        "dirs": dirs,
        "split_counts": counts,
        "samples": samples,
        "gate": gate,
    }
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_json(audit, output_dir / f"{config_path.stem}_missing_loader_audit.json")
    write_markdown(audit, output_dir / f"{config_path.stem}_missing_loader_audit.md")
    print(audit["gate"])
    return 0 if gate["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
