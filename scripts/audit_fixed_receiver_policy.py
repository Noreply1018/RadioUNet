#!/usr/bin/env python3
"""Audit official vs fixed receiver mask semantics for missing-building IRT4 loaders."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataset
from radiounet.utils import load_yaml, save_json

OUT_DIR = ROOT / "reports/full_matrix"


def tensor_hash(tensor: torch.Tensor) -> str:
    arr = tensor.detach().cpu().contiguous().numpy()
    return hashlib.sha256(arr.tobytes()).hexdigest()


def sample_config(model: str, count: int, fixed: bool) -> dict[str, Any]:
    if fixed:
        path = ROOT / f"configs/{model}_dpm_irt4_missing{count}_fixedrx_adapt.yaml"
    else:
        if model == "s":
            path = ROOT / f"configs/s_irt4_missing{count}_pool600_sparse_loss.yaml"
        else:
            path = ROOT / f"configs/c_irt4_missing{count}_sparse_loss.yaml"
    cfg = load_yaml(path)
    if count == 0:
        cfg["data"]["city_map"] = "complete"
        cfg["data"].pop("missing", None)
    return cfg


def collect(model: str, fixed: bool) -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    for count in [0, 1, 2, 4]:
        cfg = sample_config(model, count, fixed)
        ds = build_dataset(cfg, "test", smoke=True)
        item = ds[0]
        inputs, target, receiver_mask = item[0], item[1], item[2]
        rows[count] = {
            "config": f"configs/{cfg['experiment']['name']}.yaml",
            "input_shape": list(inputs.shape),
            "target_hash": tensor_hash(target),
            "tx_hash": tensor_hash(inputs[1]),
            "receiver_mask_hash": tensor_hash(receiver_mask),
            "receiver_points": int((receiver_mask[0] != 0).sum().item()),
        }
    return rows


def same_hash(rows: dict[int, dict[str, Any]], key: str) -> bool:
    values = {row[key] for row in rows.values()}
    return len(values) == 1


def write_markdown(audit: dict[str, Any]) -> None:
    lines = [
        "# Fixed Receiver Policy 审计",
        "",
        "## 结论",
        f"- fixed receiver mask 跨 missing setting 不变：`{audit['gate']['fixed_receiver_mask_stable']}`。",
        f"- target IRT4 hash 跨 missing setting 不变：`{audit['gate']['target_hash_stable']}`。",
        f"- Tx hash 跨 missing setting 不变：`{audit['gate']['tx_hash_stable']}`。",
        f"- official loader receiver mask 会随 missing building image 变化：`{audit['gate']['official_receiver_mask_changes']}`。",
        "",
        "## Hash 明细",
        "| policy | model | missing | target hash | tx hash | receiver mask hash | receiver points |",
        "| --- | --- | ---: | --- | --- | --- | ---: |",
    ]
    for policy in ["fixed", "official"]:
        for model in ["c", "s"]:
            for count, row in audit["policies"][policy][model].items():
                lines.append(
                    f"| {policy} | {model.upper()} | {count} | `{row['target_hash'][:12]}` | "
                    f"`{row['tx_hash'][:12]}` | `{row['receiver_mask_hash'][:12]}` | {row['receiver_points']} |"
                )
    lines.append("")
    lines.append(f"最终 gate：`{audit['gate']['pass']}`。")
    (OUT_DIR / "fixed_receiver_policy_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    policies = {
        "fixed": {"c": collect("c", True), "s": collect("s", True)},
        "official": {"c": collect("c", False), "s": collect("s", False)},
    }
    gate = {
        "fixed_receiver_mask_stable": all(same_hash(policies["fixed"][model], "receiver_mask_hash") for model in ["c", "s"]),
        "target_hash_stable": all(same_hash(policies["fixed"][model], "target_hash") for model in ["c", "s"]),
        "tx_hash_stable": all(same_hash(policies["fixed"][model], "tx_hash") for model in ["c", "s"]),
        "official_receiver_mask_changes": any(
            not same_hash(policies["official"][model], "receiver_mask_hash") for model in ["c", "s"]
        ),
    }
    gate["pass"] = all(gate.values())
    audit = {"policies": policies, "gate": gate}
    save_json(audit, OUT_DIR / "fixed_receiver_policy_audit.json")
    write_markdown(audit)
    print(f"fixed receiver gate: {gate['pass']}")
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
