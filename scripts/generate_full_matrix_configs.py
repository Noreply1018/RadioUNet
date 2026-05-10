#!/usr/bin/env python3
"""Generate config files needed by the full-matrix reproduction plan."""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs"


BASE_TRAINING = {
    "epochs": 50,
    "optimizer": "Adam",
    "learning_rate": 0.0001,
    "scheduler": "StepLR",
    "step_size": 30,
    "gamma": 0.1,
    "loss": "MSELoss",
}


def write_config(name: str, cfg: dict) -> None:
    path = CONFIG_DIR / f"{name}.yaml"
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)


def base_config(
    name: str,
    description: str,
    loader: str,
    simulation: str,
    inputs: int,
    num_tx: int,
    target_scale: int | None = None,
    cars_simulation: str = "no",
    cars_input: str = "no",
    city_map: str = "complete",
    missing: int | None = None,
    extra_data: dict | None = None,
    extra_training: dict | None = None,
    extra_evaluation: dict | None = None,
) -> dict:
    data = {
        "dataset_dir": "RadioMapSeer/",
        "loader": loader,
        "simulation": simulation,
        "city_map": city_map,
        "cars_simulation": cars_simulation,
        "cars_input": cars_input,
        "num_tx": num_tx,
        "threshold": 0.2,
        "batch_size": 15,
        "num_workers": 1,
        "smoke_num_tx": min(num_tx, 2),
    }
    if target_scale is not None:
        data["target_scale"] = target_scale
    if missing is not None:
        data["missing"] = missing
    if extra_data:
        data.update(extra_data)

    training = copy.deepcopy(BASE_TRAINING)
    if extra_training:
        training.update(extra_training)

    evaluation = {
        "metrics": ["mse", "nmse", "rmse"],
        "save_prediction_panels": True,
        "measure_runtime": True,
    }
    if extra_evaluation:
        evaluation.update(extra_evaluation)

    return {
        "experiment": {"name": name, "description": description, "seed": 42},
        "data": data,
        "model": {"class_name": "RadioWNet", "inputs": inputs, "phases": ["firstU", "secondU"]},
        "training": training,
        "evaluation": evaluation,
    }


def coarse_configs() -> None:
    specs = [
        ("c_irt2_thr2", "RadioUNet_C clean-map IRT2 coarse simulation.", "RadioUNet_c", "IRT2", 2, 80, None, {}),
        (
            "s_irt2_thr2_rand1_300",
            "RadioUNet_S clean-map IRT2 with random 1..300 input samples.",
            "RadioUNet_s",
            "IRT2",
            3,
            80,
            256,
            {"fix_samples": 0, "num_samples_low": 1, "num_samples_high": 301},
        ),
        (
            "c_rand_thr2",
            "RadioUNet_C clean-map random DPM/IRT2 coarse simulation.",
            "RadioUNet_c",
            "rand",
            2,
            80,
            None,
            {"IRT2maxW": 1.0},
        ),
        (
            "s_rand_thr2_rand1_300",
            "RadioUNet_S clean-map random DPM/IRT2 coarse simulation with random 1..300 input samples.",
            "RadioUNet_s",
            "rand",
            3,
            80,
            256,
            {"IRT2maxW": 1.0, "fix_samples": 0, "num_samples_low": 1, "num_samples_high": 301},
        ),
    ]
    for name, description, loader, simulation, inputs, num_tx, target_scale, extra_data in specs:
        write_config(
            name,
            base_config(name, description, loader, simulation, inputs, num_tx, target_scale, extra_data=extra_data),
        )


def cars_configs() -> None:
    specs = [
        ("c_dpmcars_thr2", "RadioUNet_C DPM cars target without cars input.", "RadioUNet_c", "DPM", 2, None),
        ("c_irt2cars_thr2", "RadioUNet_C IRT2 cars target without cars input.", "RadioUNet_c", "IRT2", 2, None),
        ("s_dpmcars_carinput_thr2_rand1_300", "RadioUNet_S DPM cars target with cars input channel.", "RadioUNet_s", "DPM", 4, 256),
        ("s_irt2cars_carinput_thr2_rand1_300", "RadioUNet_S IRT2 cars target with cars input channel.", "RadioUNet_s", "IRT2", 4, 256),
    ]
    for name, description, loader, simulation, inputs, target_scale in specs:
        extra_data = {}
        if loader == "RadioUNet_s":
            extra_data.update({"fix_samples": 0, "num_samples_low": 1, "num_samples_high": 301})
        write_config(
            name,
            base_config(
                name,
                description,
                loader,
                simulation,
                inputs,
                80,
                target_scale,
                cars_simulation="yes",
                cars_input="yes" if inputs > 2 else "no",
                extra_data=extra_data,
            ),
        )


def transfer_configs() -> None:
    sources = {
        "dpm": {
            "c_firstu": "reports/c_dpm_thr2/20260506_182311/checkpoints/firstU.pt",
            "s_firstu": "reports/s_dpm_thr2/rand1_300_50ep/checkpoints/firstU.pt",
            "target": "DPM",
        },
        "irt2": {
            "c_firstu": "reports/full_matrix/c_irt2_thr2_50ep/checkpoints/firstU.pt",
            "s_firstu": "reports/full_matrix/s_irt2_thr2_rand1_300_50ep/checkpoints/firstU.pt",
            "target": "IRT2",
        },
        "rand": {
            "c_firstu": "reports/full_matrix/c_rand_thr2_50ep/checkpoints/firstU.pt",
            "s_firstu": "reports/full_matrix/s_rand_thr2_rand1_300_50ep/checkpoints/firstU.pt",
            "target": "random coarse simulation",
        },
    }
    for source, meta in sources.items():
        for model, loader, inputs, data_extra, source_key in [
            ("c", "RadioUNet_c_sprseIRT4", 2, {"num_samples": 300}, "c_firstu"),
            (
                "s",
                "RadioUNet_s_sprseIRT4",
                3,
                {"data_samples": 600, "fix_samples": 0, "num_samples_low": 1, "num_samples_high": 301, "target_scale": 256},
                "s_firstu",
            ),
        ]:
            for mode in ["zeroshot", "adapt"]:
                name = f"{model}_{source}_irt4_{mode}"
                training = {}
                phases = ["secondU"]
                target_scale = data_extra.get("target_scale")
                clean_data_extra = {key: value for key, value in data_extra.items() if key != "target_scale"}
                if mode == "adapt":
                    training = {
                        "adaptation_mode": "secondU-only",
                        "init_checkpoint": meta[source_key],
                        "loss_mode": "sparse_mse",
                        "num_samples_for_loss": 600 if model == "s" else 300,
                    }
                cfg = base_config(
                    name,
                    f"RadioUNet_{model.upper()} {source} source {mode} evaluation/adaptation on IRT4.",
                    loader,
                    "IRT4",
                    inputs,
                    2,
                    target_scale,
                    extra_data=copy.deepcopy(clean_data_extra),
                    extra_training=training,
                    extra_evaluation={
                        "source_checkpoint": meta[source_key],
                        "source_training_target": meta["target"],
                        "target": "IRT4",
                        "tx_note": "IRT4 files are fixed to Tx indices 0 and 1 via num_tx=2.",
                    },
                )
                cfg["model"]["phases"] = phases
                write_config(name, cfg)


def missing_fixed_receiver_configs() -> None:
    for count in [0, 1, 2, 4]:
        for model, loader, inputs, extra_data, scale, samples_for_loss, source_ckpt in [
            (
                "c",
                "RadioUNet_c_sprseIRT4",
                2,
                {"num_samples": 300, "receiver_seed_policy": "fixed_map"},
                None,
                300,
                "reports/c_dpm_thr2/20260506_182311/checkpoints/firstU.pt",
            ),
            (
                "s",
                "RadioUNet_s_sprseIRT4",
                3,
                {
                    "data_samples": 600,
                    "fix_samples": 0,
                    "num_samples_low": 1,
                    "num_samples_high": 301,
                    "receiver_seed_policy": "fixed_map",
                },
                256,
                600,
                "reports/s_dpm_thr2/rand1_300_50ep/checkpoints/firstU.pt",
            ),
        ]:
            name = f"{model}_dpm_irt4_missing{count}_fixedrx_adapt"
            write_config(
                name,
                base_config(
                    name,
                    f"RadioUNet_{model.upper()} DPM-source IRT4 missing{count} sparse adaptation with fixed receiver mask.",
                    loader,
                    "IRT4",
                    inputs,
                    2,
                    scale,
                    city_map="complete" if count == 0 else "missing",
                    missing=count if count else None,
                    extra_data=extra_data,
                    extra_training={
                        "adaptation_mode": "secondU-only",
                        "init_checkpoint": source_ckpt,
                        "loss_mode": "sparse_mse",
                        "num_samples_for_loss": samples_for_loss,
                    },
                    extra_evaluation={
                        "source_checkpoint": source_ckpt,
                        "source_training_target": "DPM",
                        "target": "IRT4",
                        "receiver_policy": "paper-faithful fixed receiver mask",
                    },
                ),
            )


def main() -> int:
    coarse_configs()
    cars_configs()
    transfer_configs()
    missing_fixed_receiver_configs()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
