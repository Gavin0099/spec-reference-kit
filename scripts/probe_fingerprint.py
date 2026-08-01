#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spec_ref.io import SpecRefError, load_yaml
from spec_ref.validators import probe_fingerprints


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Source Vault artifacts with registered fingerprints.")
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--vault-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        errors = probe_fingerprints(load_yaml(args.registry.resolve()), args.vault_root.resolve())
    except SpecRefError as exc:
        errors = [str(exc)]
    if errors:
        print("[fingerprint-probe] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[fingerprint-probe] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

