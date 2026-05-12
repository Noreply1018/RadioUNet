#!/usr/bin/env python3
"""Execute remaining full-run commands in small, explicit batches."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "reports/full_matrix/remaining_full_run_commands.json"


def load_plan() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", help="Only include one group, e.g. cars, missing_fixed_receiver, wnet_size, threshold, split.")
    parser.add_argument("--name", help="Only include one command name.")
    parser.add_argument("--limit", type=int, default=1, help="Maximum commands to execute/print.")
    parser.add_argument("--execute", action="store_true", help="Actually run commands. Default is dry-run.")
    args = parser.parse_args()

    plan = load_plan()
    commands = plan.get("commands", [])
    if args.group:
        commands = [row for row in commands if row["group"] == args.group]
    if args.name:
        commands = [row for row in commands if row["name"] == args.name]
    commands = commands[: max(args.limit, 0)]

    if not commands:
        print("no commands selected")
        return 0

    for row in commands:
        print(f"[{row['group']}] {row['name']}: {row['reason']}")
        print("$ " + row["command"])
        print("skip guard: " + row["skip_guard"])
        if args.execute:
            subprocess.run(shlex.split(row["command"]), cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
