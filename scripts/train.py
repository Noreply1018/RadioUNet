#!/usr/bin/env python3
"""Train RadioUNet experiments from a YAML config."""

from __future__ import annotations

import argparse
import copy
import sys
import time
from collections import defaultdict
from pathlib import Path

import torch
import torch.optim as optim
from torch.optim import lr_scheduler

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataloader, build_model
from radiounet.metrics import mse
from radiounet.utils import (
    copy_config,
    ensure_dir,
    get_device,
    git_commit,
    load_yaml,
    require_dataset_dir,
    save_json,
    set_seed,
    timestamp,
)


def train_one_phase(
    config: dict,
    config_path: Path,
    phase_name: str,
    device: torch.device,
    run_dir: Path,
    smoke: bool,
    epochs: int,
    init_checkpoint: Path | None = None,
) -> Path:
    model = build_model(config, phase=phase_name).to(device)
    if init_checkpoint is not None:
        checkpoint = torch.load(init_checkpoint, map_location=device)
        state_dict = checkpoint.get("model_state_dict", checkpoint)
        model.load_state_dict(state_dict)

    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=float(config["training"]["learning_rate"]))
    scheduler = lr_scheduler.StepLR(
        optimizer,
        step_size=int(config["training"].get("step_size", 30)),
        gamma=float(config["training"].get("gamma", 0.1)),
    )

    dataloaders = {
        "train": build_dataloader(config, "train", smoke=smoke, shuffle=True),
        "val": build_dataloader(config, "val", smoke=smoke, shuffle=False),
    }

    best_model_wts = copy.deepcopy(model.state_dict())
    best_loss = float("inf")
    history: list[dict] = []

    for epoch in range(epochs):
        print(f"Epoch {epoch}/{epochs - 1} [{phase_name}]")
        since = time.time()

        for split in ["train", "val"]:
            if split == "train":
                scheduler.step()
                model.train()
                lr = optimizer.param_groups[0]["lr"]
                print(f"learning rate {lr}")
            else:
                model.eval()

            metrics = defaultdict(float)
            epoch_samples = 0

            for batch_idx, (inputs, targets) in enumerate(dataloaders[split]):
                inputs = inputs.to(device)
                targets = targets.to(device)
                optimizer.zero_grad()

                with torch.set_grad_enabled(split == "train"):
                    outputs1, outputs2 = model(inputs)
                    pred = outputs1 if phase_name == "firstU" else outputs2
                    loss = mse(pred, targets)
                    if split == "train":
                        loss.backward()
                        optimizer.step()

                batch_size = inputs.size(0)
                metrics["loss"] += float(loss.detach().cpu()) * batch_size
                epoch_samples += batch_size
                if smoke and batch_idx >= 1:
                    break

            epoch_loss = metrics["loss"] / max(epoch_samples, 1)
            history.append({"epoch": epoch, "split": split, "loss": epoch_loss, "samples": epoch_samples})
            print(f"{split}: loss={epoch_loss:.6f}, samples={epoch_samples}")
            if split == "val" and epoch_loss < best_loss:
                best_loss = epoch_loss
                best_model_wts = copy.deepcopy(model.state_dict())

        elapsed = time.time() - since
        print(f"epoch time {elapsed // 60:.0f}m {elapsed % 60:.0f}s")

    model.load_state_dict(best_model_wts)
    checkpoint_dir = ensure_dir(run_dir / "checkpoints")
    checkpoint_path = checkpoint_dir / f"{phase_name}.pt"
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "phase": phase_name,
            "best_val_loss": best_loss,
            "config": config,
            "config_path": str(config_path),
            "git_commit": git_commit(),
            "smoke": smoke,
        },
        checkpoint_path,
    )
    save_json({"phase": phase_name, "best_val_loss": best_loss, "history": history}, run_dir / f"{phase_name}_history.json")
    print(f"saved checkpoint: {checkpoint_path}")
    return checkpoint_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Experiment YAML config.")
    parser.add_argument("--phase", choices=["firstU", "secondU", "both"], default="firstU")
    parser.add_argument("--init-checkpoint", help="Checkpoint used to initialize secondU.")
    parser.add_argument("--device", default="auto", help="auto, cpu, cuda, or cuda:N.")
    parser.add_argument("--epochs", type=int, help="Override epoch count.")
    parser.add_argument("--smoke", action="store_true", help="Use a tiny custom subset and short training.")
    parser.add_argument("--run-dir", help="Output directory. Defaults to reports/<experiment>/<timestamp>.")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_yaml(config_path)
    try:
        require_dataset_dir(config)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    set_seed(int(config.get("experiment", {}).get("seed", 42)))
    device = get_device(args.device)
    epochs = args.epochs if args.epochs is not None else int(config["training"].get("epochs", 50))
    if args.smoke:
        epochs = min(epochs, 1)

    experiment_name = config.get("experiment", {}).get("name", "radiounet")
    run_dir = Path(args.run_dir) if args.run_dir else Path("reports") / experiment_name / timestamp()
    ensure_dir(run_dir)
    copy_config(config_path, run_dir)
    save_json({"config": config, "git_commit": git_commit(), "device": str(device), "smoke": args.smoke}, run_dir / "run_metadata.json")

    print(f"device: {device}")
    print(f"run_dir: {run_dir}")

    if args.phase in {"firstU", "both"}:
        first_checkpoint = train_one_phase(config, config_path, "firstU", device, run_dir, args.smoke, epochs)
    else:
        first_checkpoint = Path(args.init_checkpoint) if args.init_checkpoint else None

    if args.phase in {"secondU", "both"}:
        if first_checkpoint is None:
            raise ValueError("--init-checkpoint is required when training secondU directly.")
        train_one_phase(config, config_path, "secondU", device, run_dir, args.smoke, epochs, init_checkpoint=first_checkpoint)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
