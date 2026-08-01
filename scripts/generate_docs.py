#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spec_ref.generate import generate_outputs
from spec_ref.io import SpecRefError


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or verify manifest and Markdown views.")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        mismatches = generate_outputs(args.repo.resolve(), check=args.check)
    except SpecRefError as exc:
        print(f"[generation] FAIL\n{exc}")
        return 1
    if mismatches:
        print("[generation] STALE")
        for path in mismatches:
            print(f"- {path}")
        return 1
    print("[generation] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

