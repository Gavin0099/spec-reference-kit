from __future__ import annotations

import hashlib
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from spec_ref.generate import generate_outputs
from spec_ref.io import SpecRefError, dump_yaml_atomic, load_yaml
from spec_ref.promotion import promote_entry
from spec_ref.validators import (
    load_authority_levels,
    probe_fingerprints,
    validate_proposal,
    validate_repository,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def make_workspace(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        for directory in ("contract", "sources", "proposals", "evidence"):
            shutil.copytree(REPO_ROOT / directory, root / directory)
        (root / "tables").mkdir()
        shutil.copy2(
            REPO_ROOT / "tables" / "register_matrix.empty.yaml",
            root / "tables" / "register_matrix.yaml",
        )
        return temp, root

    def test_checked_in_repository_is_valid(self) -> None:
        self.assertEqual([], validate_repository(REPO_ROOT))
        self.assertEqual([], generate_outputs(REPO_ROOT, check=True))

    def test_manifest_fingerprints_the_lf_table_bytes(self) -> None:
        # Git stores the table with LF; a fingerprint taken over a CRLF working
        # copy passes on Windows and fails on every Linux checkout.
        manifest = load_yaml(REPO_ROOT / "exports" / "governed_surface_manifest.yaml")
        table_bytes = (REPO_ROOT / "tables" / "register_matrix.yaml").read_bytes()
        lf_sha = hashlib.sha256(table_bytes.replace(b"\r\n", b"\n")).hexdigest()
        self.assertEqual(lf_sha, manifest["governed_tables"][0]["sha256"])

    def test_writers_emit_lf_on_every_platform(self) -> None:
        temp, root = self.make_workspace()
        with temp:
            table = root / "tables" / "written.yaml"
            dump_yaml_atomic(table, {"entries": [{"id": "a"}, {"id": "b"}]})
            self.assertNotIn(b"\r", table.read_bytes())
            generate_outputs(root)
            for relative in ("exports/governed_surface_manifest.yaml", "specs/generated/register-map.md"):
                self.assertNotIn(b"\r", (root / relative).read_bytes(), relative)

    def test_source_vault_fingerprint_matches(self) -> None:
        registry = load_yaml(REPO_ROOT / "sources" / "source_registry.yaml")
        errors = probe_fingerprints(registry, REPO_ROOT / "tests" / "fixtures" / "vault")
        self.assertEqual([], errors)

    def test_human_review_receipt_promotes_proposal(self) -> None:
        temp, root = self.make_workspace()
        self.addCleanup(temp.cleanup)
        entry = promote_entry(
            root,
            root / "proposals" / "register_map" / "demo_reg_0082_bit3.yaml",
            root / "evidence" / "review_packets" / "REV-DEMO-0001.yaml",
            root / "tables" / "register_matrix.yaml",
        )
        self.assertEqual("approved", entry["review"]["status"])
        table = load_yaml(root / "tables" / "register_matrix.yaml")
        self.assertEqual(["demo_reg_0082_bit3"], [item["entry_id"] for item in table["entries"]])

    def test_ai_reviewer_receipt_is_rejected(self) -> None:
        temp, root = self.make_workspace()
        self.addCleanup(temp.cleanup)
        receipt_path = root / "evidence" / "review_packets" / "REV-DEMO-0001.yaml"
        receipt = load_yaml(receipt_path)
        receipt["reviewer_id"] = "ai"
        receipt["reviewer_type"] = "ai"
        dump_yaml_atomic(receipt_path, receipt)
        with self.assertRaisesRegex(SpecRefError, "reviewer_type human"):
            promote_entry(
                root,
                root / "proposals" / "register_map" / "demo_reg_0082_bit3.yaml",
                receipt_path,
                root / "tables" / "register_matrix.yaml",
            )

    def test_source_hash_mismatch_is_rejected(self) -> None:
        proposal = deepcopy(
            load_yaml(REPO_ROOT / "proposals" / "register_map" / "demo_reg_0082_bit3.yaml")
        )
        proposal["source"]["artifact_sha256"] = "0" * 64
        registry = load_yaml(REPO_ROOT / "sources" / "source_registry.yaml")
        extraction = load_yaml(
            REPO_ROOT / "evidence" / "extraction_receipts" / "EXTRACT-DEMO-0001.yaml"
        )
        levels, statuses = load_authority_levels(
            REPO_ROOT / "contract" / "authority_levels.yaml"
        )
        errors = validate_proposal(proposal, registry, levels, statuses, extraction)
        self.assertIn("proposal source fingerprint does not match registry", errors)
        self.assertIn(
            "extraction receipt artifact fingerprint does not match proposal",
            errors,
        )

    def test_duplicate_promotion_is_rejected(self) -> None:
        with self.assertRaisesRegex(SpecRefError, "duplicate canonical entry_id"):
            promote_entry(
                REPO_ROOT,
                REPO_ROOT / "proposals" / "register_map" / "demo_reg_0082_bit3.yaml",
                REPO_ROOT / "evidence" / "review_packets" / "REV-DEMO-0001.yaml",
                REPO_ROOT / "tables" / "register_matrix.yaml",
            )

    def test_duplicate_yaml_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "duplicate.yaml"
            path.write_text("entry_id: first\nentry_id: second\n", encoding="utf-8")
            with self.assertRaisesRegex(SpecRefError, "duplicate key"):
                load_yaml(path)

    def test_review_receipt_proposal_hash_mismatch_is_rejected(self) -> None:
        temp, root = self.make_workspace()
        self.addCleanup(temp.cleanup)
        receipt_path = root / "evidence" / "review_packets" / "REV-DEMO-0001.yaml"
        receipt = load_yaml(receipt_path)
        receipt["proposal_sha256"] = "f" * 64
        dump_yaml_atomic(receipt_path, receipt)
        with self.assertRaisesRegex(SpecRefError, "proposal fingerprint"):
            promote_entry(
                root,
                root / "proposals" / "register_map" / "demo_reg_0082_bit3.yaml",
                receipt_path,
                root / "tables" / "register_matrix.yaml",
            )


if __name__ == "__main__":
    unittest.main()
