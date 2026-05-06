#!/usr/bin/env python3
"""Evaluation entry point placeholder for RadioUNet experiments."""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Experiment YAML config.")
    parser.add_argument("--checkpoint", required=True, help="Checkpoint to evaluate.")
    args = parser.parse_args()
    raise NotImplementedError(
        f"Evaluation is not implemented yet for config={args.config}, checkpoint={args.checkpoint}."
    )


if __name__ == "__main__":
    raise SystemExit(main())

