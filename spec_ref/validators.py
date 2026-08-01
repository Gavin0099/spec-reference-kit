from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from .io import SpecRefError, canonical_sha256, file_sha256, load_yaml


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ADDRESS_RE = re.compile(r"^0x[0-9A-Fa-f]+$")
BIT_RANGE_RE = re.compile(r"^(?:[0-9]+|[0-9]+:[0-9]+)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _mapping(value: Any, field: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{field} must be a mapping")
        return {}
    return value


def _list(value: Any, field: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{field} must be a list")
        return []
    return value


def _required(mapping: dict[str, Any], fields: Iterable[str], prefix: str, errors: list[str]) -> None:
    for field in fields:
        if field not in mapping or mapping[field] in (None, ""):
            errors.append(f"{prefix}.{field} is required")


def _nonempty_strings(value: Any, field: str, errors: list[str]) -> list[str]:
    items = _list(value, field, errors)
    if not items:
        errors.append(f"{field} must not be empty")
        return []
    if any(not isinstance(item, str) or not item.strip() for item in items):
        errors.append(f"{field} must contain non-empty strings")
        return []
    return items


def _valid_sha(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        errors.append(f"{field} must be a lowercase SHA-256")


def load_authority_levels(path: Path) -> tuple[set[str], set[str]]:
    payload = load_yaml(path)
    levels = payload.get("levels")
    statuses = payload.get("review_statuses")
    if not isinstance(levels, list) or not all(isinstance(item, str) for item in levels):
        raise SpecRefError(f"invalid authority levels: {path}")
    if not isinstance(statuses, list) or not all(isinstance(item, str) for item in statuses):
        raise SpecRefError(f"invalid review statuses: {path}")
    return set(levels), set(statuses)


def validate_source_registry(
    registry: dict[str, Any], authority_levels: set[str]
) -> list[str]:
    errors: list[str] = []
    if registry.get("schema_version") != "0.1":
        errors.append("source_registry.schema_version must be '0.1'")
    sources = _list(registry.get("sources"), "source_registry.sources", errors)
    seen: set[str] = set()
    for index, raw_source in enumerate(sources):
        prefix = f"source_registry.sources[{index}]"
        source = _mapping(raw_source, prefix, errors)
        _required(
            source,
            (
                "source_id",
                "title",
                "document_type",
                "product_scope",
                "revision",
                "effective_date",
                "locator",
                "authority_level",
                "classification",
                "review_owner",
            ),
            prefix,
            errors,
        )
        source_id = source.get("source_id")
        if isinstance(source_id, str):
            if source_id in seen:
                errors.append(f"duplicate source_id: {source_id}")
            seen.add(source_id)
        _nonempty_strings(source.get("product_scope"), f"{prefix}.product_scope", errors)
        if not isinstance(source.get("effective_date"), str) or not DATE_RE.fullmatch(
            source.get("effective_date", "")
        ):
            errors.append(f"{prefix}.effective_date must use YYYY-MM-DD")
        if source.get("authority_level") not in authority_levels:
            errors.append(f"{prefix}.authority_level is not declared")
        locator = _mapping(source.get("locator"), f"{prefix}.locator", errors)
        _required(locator, ("type", "artifact_id", "artifact_path", "artifact_sha256"), f"{prefix}.locator", errors)
        if locator.get("type") != "vault_artifact":
            errors.append(f"{prefix}.locator.type must be vault_artifact")
        _valid_sha(locator.get("artifact_sha256"), f"{prefix}.locator.artifact_sha256", errors)
        artifact_path = locator.get("artifact_path")
        if isinstance(artifact_path, str):
            parsed = PurePosixPath(artifact_path)
            if parsed.is_absolute() or ".." in parsed.parts:
                errors.append(f"{prefix}.locator.artifact_path must be a safe relative path")
        if not isinstance(source.get("supersedes"), list):
            errors.append(f"{prefix}.supersedes must be a list")
    return errors


def source_index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = registry.get("sources")
    if not isinstance(sources, list):
        return {}
    return {
        source["source_id"]: source
        for source in sources
        if isinstance(source, dict) and isinstance(source.get("source_id"), str)
    }


def validate_extraction_receipt(
    receipt: dict[str, Any], proposal: dict[str, Any], registered_source: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if receipt.get("schema_version") != "0.1":
        errors.append("extraction_receipt.schema_version must be '0.1'")
    _required(
        receipt,
        ("receipt_id", "source_id", "artifact_sha256", "locator", "extracted_surface_sha256", "extractor", "extracted_at"),
        "extraction_receipt",
        errors,
    )
    proposal_source = _mapping(proposal.get("source"), "proposal.source", errors)
    if receipt.get("receipt_id") != proposal_source.get("extraction_receipt_id"):
        errors.append("extraction receipt ID does not match proposal")
    if receipt.get("source_id") != proposal_source.get("source_id"):
        errors.append("extraction receipt source_id does not match proposal")
    if receipt.get("artifact_sha256") != proposal_source.get("artifact_sha256"):
        errors.append("extraction receipt artifact fingerprint does not match proposal")
    if receipt.get("extracted_surface_sha256") != proposal_source.get("extracted_surface_sha256"):
        errors.append("extraction receipt surface fingerprint does not match proposal")
    registered_locator = registered_source.get("locator", {})
    if receipt.get("artifact_sha256") != registered_locator.get("artifact_sha256"):
        errors.append("extraction receipt artifact fingerprint does not match registry")
    _valid_sha(receipt.get("artifact_sha256"), "extraction_receipt.artifact_sha256", errors)
    _valid_sha(
        receipt.get("extracted_surface_sha256"),
        "extraction_receipt.extracted_surface_sha256",
        errors,
    )
    locator = _mapping(receipt.get("locator"), "extraction_receipt.locator", errors)
    for field in ("section", "page", "table"):
        if locator.get(field) != proposal_source.get(field):
            errors.append(f"extraction receipt locator.{field} does not match proposal")
    return errors


def validate_proposal(
    proposal: dict[str, Any],
    registry: dict[str, Any],
    authority_levels: set[str],
    review_statuses: set[str],
    extraction_receipt: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    if proposal.get("schema_version") != "0.1":
        errors.append("proposal.schema_version must be '0.1'")
    _required(
        proposal,
        ("entry_id", "topic", "claim", "authority", "source", "verification_scope", "review"),
        "proposal",
        errors,
    )
    if proposal.get("topic") != "register_bit":
        errors.append("proposal.topic must be register_bit in v0.1")
    claim = _mapping(proposal.get("claim"), "proposal.claim", errors)
    _required(claim, ("register", "bit_range", "name", "encoding"), "proposal.claim", errors)
    if not isinstance(claim.get("register"), str) or not ADDRESS_RE.fullmatch(claim.get("register", "")):
        errors.append("proposal.claim.register must be a hexadecimal address")
    if not isinstance(claim.get("bit_range"), str) or not BIT_RANGE_RE.fullmatch(claim.get("bit_range", "")):
        errors.append("proposal.claim.bit_range must be N or MSB:LSB")
    encoding = _mapping(claim.get("encoding"), "proposal.claim.encoding", errors)
    if len(encoding) < 2 or any(not isinstance(key, str) for key in encoding):
        errors.append("proposal.claim.encoding must define at least two string keys")

    authority = _mapping(proposal.get("authority"), "proposal.authority", errors)
    _required(authority, ("level", "product_scope", "silicon_revision_scope"), "proposal.authority", errors)
    if authority.get("level") not in authority_levels:
        errors.append("proposal.authority.level is not declared")
    product_scope = _nonempty_strings(authority.get("product_scope"), "proposal.authority.product_scope", errors)
    _nonempty_strings(
        authority.get("silicon_revision_scope"),
        "proposal.authority.silicon_revision_scope",
        errors,
    )

    source = _mapping(proposal.get("source"), "proposal.source", errors)
    _required(
        source,
        ("source_id", "artifact_sha256", "section", "page", "table", "extraction_receipt_id", "extracted_surface_sha256"),
        "proposal.source",
        errors,
    )
    _valid_sha(source.get("artifact_sha256"), "proposal.source.artifact_sha256", errors)
    _valid_sha(
        source.get("extracted_surface_sha256"),
        "proposal.source.extracted_surface_sha256",
        errors,
    )
    registered_source = source_index(registry).get(source.get("source_id"))
    if registered_source is None:
        errors.append("proposal.source.source_id is not registered")
    else:
        locator = registered_source.get("locator", {})
        if source.get("artifact_sha256") != locator.get("artifact_sha256"):
            errors.append("proposal source fingerprint does not match registry")
        if authority.get("level") != registered_source.get("authority_level"):
            errors.append("proposal authority level does not match registered source")
        registered_scope = set(registered_source.get("product_scope", []))
        if not set(product_scope).issubset(registered_scope):
            errors.append("proposal product scope exceeds registered source scope")
        if extraction_receipt is not None:
            errors.extend(validate_extraction_receipt(extraction_receipt, proposal, registered_source))

    verification = _mapping(proposal.get("verification_scope"), "proposal.verification_scope", errors)
    _required(verification, ("claim", "excludes"), "proposal.verification_scope", errors)
    _nonempty_strings(verification.get("excludes"), "proposal.verification_scope.excludes", errors)

    review = _mapping(proposal.get("review"), "proposal.review", errors)
    _required(review, ("status", "eligible_for_promotion"), "proposal.review", errors)
    if review.get("status") not in review_statuses:
        errors.append("proposal.review.status is not declared")
    if review.get("status") != "proposed":
        errors.append("proposal.review.status must remain proposed before promotion")
    if review.get("eligible_for_promotion") is not False:
        errors.append("proposal cannot self-declare promotion eligibility")
    return errors


def validate_review_receipt(
    receipt: dict[str, Any], proposal: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if receipt.get("schema_version") != "0.1":
        errors.append("review_receipt.schema_version must be '0.1'")
    _required(
        receipt,
        (
            "receipt_id",
            "proposal_id",
            "proposal_sha256",
            "reviewer_id",
            "reviewer_type",
            "decision",
            "source_checked",
            "scope_checked",
            "reviewed_at",
            "attestation",
        ),
        "review_receipt",
        errors,
    )
    if receipt.get("proposal_id") != proposal.get("entry_id"):
        errors.append("review receipt proposal_id does not match proposal")
    if receipt.get("proposal_sha256") != canonical_sha256(proposal):
        errors.append("review receipt proposal fingerprint does not match proposal")
    if receipt.get("reviewer_type") != "human":
        errors.append("review receipt must declare reviewer_type human")
    reviewer_id = receipt.get("reviewer_id")
    if not isinstance(reviewer_id, str) or reviewer_id.strip().lower() in {"", "ai", "agent", "llm"}:
        errors.append("review receipt requires a non-AI reviewer_id")
    if receipt.get("decision") != "approved":
        errors.append("review receipt decision must be approved")
    if receipt.get("source_checked") is not True:
        errors.append("review receipt must confirm source_checked")
    if receipt.get("scope_checked") is not True:
        errors.append("review receipt must confirm scope_checked")
    if not isinstance(receipt.get("attestation"), str) or len(receipt.get("attestation", "").strip()) < 20:
        errors.append("review receipt attestation is too weak")
    return errors


def validate_canonical_table(table: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if table.get("schema_version") != "0.1":
        errors.append("canonical_table.schema_version must be '0.1'")
    if table.get("entry_type") != "register_bit":
        errors.append("canonical_table.entry_type must be register_bit")
    entries = _list(table.get("entries"), "canonical_table.entries", errors)
    seen: set[str] = set()
    for index, raw_entry in enumerate(entries):
        prefix = f"canonical_table.entries[{index}]"
        entry = _mapping(raw_entry, prefix, errors)
        entry_id = entry.get("entry_id")
        if not isinstance(entry_id, str) or not entry_id:
            errors.append(f"{prefix}.entry_id is required")
        elif entry_id in seen:
            errors.append(f"duplicate canonical entry_id: {entry_id}")
        else:
            seen.add(entry_id)
        review = _mapping(entry.get("review"), f"{prefix}.review", errors)
        if review.get("status") != "approved":
            errors.append(f"{prefix}.review.status must be approved")
        promotion = _mapping(entry.get("promotion"), f"{prefix}.promotion", errors)
        _required(
            promotion,
            ("proposal_id", "proposal_sha256", "review_receipt_id", "promoted_at"),
            f"{prefix}.promotion",
            errors,
        )
    return errors


def validate_manifest(manifest: dict[str, Any], repo_root: Path) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != "0.1":
        errors.append("manifest.schema_version must be '0.1'")
    tables = _list(manifest.get("governed_tables"), "manifest.governed_tables", errors)
    for index, raw_table in enumerate(tables):
        table_ref = _mapping(raw_table, f"manifest.governed_tables[{index}]", errors)
        _required(
            table_ref,
            ("id", "path", "schema", "state", "approved_entries", "sha256"),
            f"manifest.governed_tables[{index}]",
            errors,
        )
        relative_path = table_ref.get("path")
        if not isinstance(relative_path, str):
            continue
        table_path = repo_root / relative_path
        try:
            actual_sha = file_sha256(table_path)
            table = load_yaml(table_path)
        except SpecRefError as exc:
            errors.append(str(exc))
            continue
        if table_ref.get("sha256") != actual_sha:
            errors.append(f"manifest table fingerprint mismatch: {relative_path}")
        entries = table.get("entries")
        if isinstance(entries, list) and table_ref.get("approved_entries") != len(entries):
            errors.append(f"manifest approved entry count mismatch: {relative_path}")
    usage = _mapping(manifest.get("consumer_usage"), "manifest.consumer_usage", errors)
    _nonempty_strings(usage.get("allowed"), "manifest.consumer_usage.allowed", errors)
    _nonempty_strings(usage.get("forbidden"), "manifest.consumer_usage.forbidden", errors)
    return errors


def probe_fingerprints(registry: dict[str, Any], vault_root: Path) -> list[str]:
    errors: list[str] = []
    for source_id, source in source_index(registry).items():
        locator = source.get("locator", {})
        relative = locator.get("artifact_path")
        if not isinstance(relative, str):
            errors.append(f"{source_id}: artifact_path missing")
            continue
        artifact = vault_root / relative
        try:
            actual = file_sha256(artifact)
        except SpecRefError as exc:
            errors.append(f"{source_id}: {exc}")
            continue
        if actual != locator.get("artifact_sha256"):
            errors.append(f"{source_id}: source fingerprint mismatch")
    return errors


def validate_repository(repo_root: Path) -> list[str]:
    errors: list[str] = []
    try:
        authority_levels, review_statuses = load_authority_levels(
            repo_root / "contract" / "authority_levels.yaml"
        )
        registry = load_yaml(repo_root / "sources" / "source_registry.yaml")
    except SpecRefError as exc:
        return [str(exc)]
    errors.extend(validate_source_registry(registry, authority_levels))

    proposals: dict[str, dict[str, Any]] = {}
    for proposal_path in sorted((repo_root / "proposals").glob("**/*.yaml")):
        try:
            proposal = load_yaml(proposal_path)
        except SpecRefError as exc:
            errors.append(str(exc))
            continue
        proposal_id = proposal.get("entry_id")
        if isinstance(proposal_id, str):
            proposals[proposal_id] = proposal
        receipt_id = proposal.get("source", {}).get("extraction_receipt_id")
        extraction = None
        if isinstance(receipt_id, str):
            try:
                extraction = load_yaml(
                    repo_root / "evidence" / "extraction_receipts" / f"{receipt_id}.yaml"
                )
            except SpecRefError as exc:
                errors.append(str(exc))
        for issue in validate_proposal(
            proposal,
            registry,
            authority_levels,
            review_statuses,
            extraction,
        ):
            errors.append(f"{proposal_path.relative_to(repo_root)}: {issue}")

    review_receipts: dict[str, dict[str, Any]] = {}
    for receipt_path in sorted((repo_root / "evidence" / "review_packets").glob("*.yaml")):
        try:
            receipt = load_yaml(receipt_path)
        except SpecRefError as exc:
            errors.append(str(exc))
            continue
        receipt_id = receipt.get("receipt_id")
        proposal = proposals.get(receipt.get("proposal_id"))
        if proposal is None:
            errors.append(f"{receipt_path.relative_to(repo_root)}: referenced proposal not found")
            continue
        if isinstance(receipt_id, str):
            review_receipts[receipt_id] = receipt
        for issue in validate_review_receipt(receipt, proposal):
            errors.append(f"{receipt_path.relative_to(repo_root)}: {issue}")

    for table_path in sorted((repo_root / "tables").glob("*.yaml")):
        if table_path.name.endswith(".empty.yaml"):
            continue
        try:
            table = load_yaml(table_path)
        except SpecRefError as exc:
            errors.append(str(exc))
            continue
        for issue in validate_canonical_table(table):
            errors.append(f"{table_path.relative_to(repo_root)}: {issue}")
        for entry in table.get("entries", []):
            if not isinstance(entry, dict):
                continue
            promotion = entry.get("promotion", {})
            proposal = proposals.get(promotion.get("proposal_id"))
            receipt = review_receipts.get(promotion.get("review_receipt_id"))
            if proposal is None:
                errors.append(f"{table_path.relative_to(repo_root)}: canonical proposal not found")
                continue
            if receipt is None:
                errors.append(f"{table_path.relative_to(repo_root)}: canonical review receipt not found")
                continue
            for field in ("entry_id", "topic", "claim", "authority", "source", "verification_scope"):
                if entry.get(field) != proposal.get(field):
                    errors.append(
                        f"{table_path.relative_to(repo_root)}: canonical {field} differs from proposal"
                    )
            if promotion.get("proposal_sha256") != canonical_sha256(proposal):
                errors.append(f"{table_path.relative_to(repo_root)}: canonical proposal hash mismatch")
            if receipt.get("proposal_sha256") != promotion.get("proposal_sha256"):
                errors.append(f"{table_path.relative_to(repo_root)}: receipt/promotion hash mismatch")

    try:
        manifest = load_yaml(repo_root / "exports" / "governed_surface_manifest.yaml")
        errors.extend(validate_manifest(manifest, repo_root))
    except SpecRefError as exc:
        errors.append(str(exc))
    return errors

