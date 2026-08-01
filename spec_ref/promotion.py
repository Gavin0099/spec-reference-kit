from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .io import SpecRefError, canonical_sha256, dump_yaml_atomic, is_within, load_yaml
from .validators import (
    load_authority_levels,
    validate_canonical_table,
    validate_proposal,
    validate_review_receipt,
)


def promote_entry(
    repo_root: Path,
    proposal_path: Path,
    review_receipt_path: Path,
    table_path: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    proposal_path = proposal_path.resolve()
    review_receipt_path = review_receipt_path.resolve()
    table_path = table_path.resolve()
    if not is_within(proposal_path, repo_root / "proposals"):
        raise SpecRefError("proposal must be under proposals/")
    if not is_within(review_receipt_path, repo_root / "evidence" / "review_packets"):
        raise SpecRefError("review receipt must be under evidence/review_packets/")

    authority_levels, review_statuses = load_authority_levels(
        repo_root / "contract" / "authority_levels.yaml"
    )
    registry = load_yaml(repo_root / "sources" / "source_registry.yaml")
    proposal = load_yaml(proposal_path)
    receipt = load_yaml(review_receipt_path)
    extraction_id = proposal.get("source", {}).get("extraction_receipt_id")
    if not isinstance(extraction_id, str):
        raise SpecRefError("proposal extraction_receipt_id is required")
    extraction = load_yaml(
        repo_root / "evidence" / "extraction_receipts" / f"{extraction_id}.yaml"
    )

    errors = validate_proposal(
        proposal,
        registry,
        authority_levels,
        review_statuses,
        extraction,
    )
    errors.extend(validate_review_receipt(receipt, proposal))
    if errors:
        raise SpecRefError("promotion rejected:\n- " + "\n- ".join(errors))

    table = load_yaml(table_path)
    table_errors = validate_canonical_table(table)
    if table_errors:
        raise SpecRefError("canonical table invalid:\n- " + "\n- ".join(table_errors))
    entries = table.setdefault("entries", [])
    entry_id = proposal["entry_id"]
    if any(isinstance(entry, dict) and entry.get("entry_id") == entry_id for entry in entries):
        raise SpecRefError(f"duplicate canonical entry_id: {entry_id}")

    canonical = {
        key: deepcopy(proposal[key])
        for key in ("entry_id", "topic", "claim", "authority", "source", "verification_scope")
    }
    canonical["review"] = {
        "status": "approved",
        "reviewer_id": receipt["reviewer_id"],
        "reviewed_at": receipt["reviewed_at"],
    }
    canonical["promotion"] = {
        "proposal_id": entry_id,
        "proposal_sha256": canonical_sha256(proposal),
        "review_receipt_id": receipt["receipt_id"],
        "promoted_at": receipt["reviewed_at"],
    }
    entries.append(canonical)
    entries.sort(key=lambda entry: entry["entry_id"])
    dump_yaml_atomic(table_path, table)
    return canonical

