#!/usr/bin/env python3
"""Training entry point placeholder for config-driven RadioUNet experiments."""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Experiment YAML config.")
    args = parser.parse_args()
    raise NotImplementedError(
        f"Training is not implemented yet. Next step: wire {args.config} to src/radiounet data and model modules."
    )


if __name__ == "__main__":
    raise SystemExit(main())

