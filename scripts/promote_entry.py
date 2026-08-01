#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spec_ref.io import SpecRefError
from spec_ref.promotion import promote_entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote a reviewed proposal into a canonical table.")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--review-receipt", type=Path, required=True)
    parser.add_argument("--table", type=Path, required=True)
    args = parser.parse_args()
    try:
        entry = promote_entry(
            args.repo.resolve(),
            args.proposal.resolve(),
            args.review_receipt.resolve(),
            args.table.resolve(),
        )
    except SpecRefError as exc:
        print(f"[promotion] REJECTED\n{exc}")
        return 1
    print(f"[promotion] APPROVED entry_id={entry['entry_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

