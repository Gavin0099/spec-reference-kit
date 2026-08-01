#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spec_ref.generate import generate_outputs
from spec_ref.io import SpecRefError, load_yaml
from spec_ref.validators import probe_fingerprints, validate_repository


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate governed spec-reference surfaces.")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--vault-root", type=Path)
    parser.add_argument("--check-generated", action="store_true")
    args = parser.parse_args()
    repo_root = args.repo.resolve()
    errors = validate_repository(repo_root)
    if args.vault_root:
        try:
            registry = load_yaml(repo_root / "sources" / "source_registry.yaml")
            errors.extend(probe_fingerprints(registry, args.vault_root.resolve()))
        except SpecRefError as exc:
            errors.append(str(exc))
    if args.check_generated:
        try:
            for path in generate_outputs(repo_root, check=True):
                errors.append(f"generated output is stale: {path}")
        except SpecRefError as exc:
            errors.append(str(exc))
    if errors:
        print("[spec-reference-validation] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[spec-reference-validation] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

