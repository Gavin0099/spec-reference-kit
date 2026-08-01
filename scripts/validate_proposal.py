#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spec_ref.io import SpecRefError, load_yaml
from spec_ref.validators import load_authority_levels, validate_proposal


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate one proposal and extraction receipt.")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--proposal", type=Path, required=True)
    args = parser.parse_args()
    repo_root = args.repo.resolve()
    try:
        proposal = load_yaml(args.proposal.resolve())
        registry = load_yaml(repo_root / "sources" / "source_registry.yaml")
        levels, statuses = load_authority_levels(repo_root / "contract" / "authority_levels.yaml")
        receipt_id = proposal.get("source", {}).get("extraction_receipt_id")
        extraction = load_yaml(
            repo_root / "evidence" / "extraction_receipts" / f"{receipt_id}.yaml"
        )
        errors = validate_proposal(proposal, registry, levels, statuses, extraction)
    except SpecRefError as exc:
        errors = [str(exc)]
    if errors:
        print("[proposal-validation] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[proposal-validation] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

