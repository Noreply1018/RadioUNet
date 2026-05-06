#!/usr/bin/env python3
"""Generate RadioUNet sample and prediction panels."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radiounet.factory import build_dataloader, build_model
from radiounet.utils import ensure_dir, get_device, load_yaml, require_dataset_dir


def to_image(tensor: torch.Tensor) -> np.ndarray:
    arr = tensor.detach().cpu().numpy()
    if arr.ndim == 3:
        arr = arr[0]
    return arr


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint")
    parser.add_argument("--split", choices=["train", "val", "test"], default="test")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--output-dir", default="reports/figures")
    args = parser.parse_args()

    config = load_yaml(args.config)
    try:
        require_dataset_dir(config)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    device = get_device(args.device)
    loader = build_dataloader(config, args.split, smoke=args.smoke, shuffle=False)
    model = None
    checkpoint_phase = None
    if args.checkpoint:
        checkpoint = torch.load(args.checkpoint, map_location=device)
        checkpoint_phase = checkpoint.get("phase", "secondU")
        model = build_model(config, phase=checkpoint_phase).to(device)
        model.load_state_dict(checkpoint.get("model_state_dict", checkpoint))
        model.eval()

    output_dir = ensure_dir(args.output_dir)
    count = 0
    with torch.no_grad():
        for inputs, targets in loader:
            inputs = inputs.to(device)
            targets = targets.to(device)
            prediction = None
            if model is not None:
                outputs1, outputs2 = model(inputs)
                prediction = outputs1 if checkpoint_phase == "firstU" else outputs2

            for i in range(inputs.size(0)):
                building = to_image(inputs[i, 0])
                tx = to_image(inputs[i, 1])
                target = to_image(targets[i])
                panels = [("building", building), ("tx", tx), ("target", target)]
                if prediction is not None:
                    pred = to_image(prediction[i])
                    panels.extend([("prediction", pred), ("abs error", np.abs(pred - target))])

                fig, axes = plt.subplots(1, len(panels), figsize=(4 * len(panels), 4), constrained_layout=True)
                if len(panels) == 1:
                    axes = [axes]
                for ax, (title, image) in zip(axes, panels):
                    ax.imshow(image, cmap="viridis")
                    ax.set_title(title)
                    ax.axis("off")
                out = output_dir / f"{config['experiment']['name']}_{args.split}_{count:04d}.png"
                fig.savefig(out, dpi=150)
                plt.close(fig)
                print(f"saved figure: {out}")
                count += 1
                if count >= args.limit:
                    return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
