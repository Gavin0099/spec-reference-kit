from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import package_disconnected_bundle as bundle
from scripts.package_disconnected_bundle import write_manifest


CANONICAL_URL = "https://example.invalid/ai-governance-framework.git"


class DisconnectedBundleTests(unittest.TestCase):
    def make_workspace(self, *, adopted_commit: str = "framework-head", framework_repo: str = CANONICAL_URL) -> tuple[tempfile.TemporaryDirectory, Path, Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name) / "repo"
        framework = root / "ai-governance-framework"
        framework.mkdir(parents=True)
        (root / "governance").mkdir()
        (root / "requirements.txt").write_text("PyYAML==6.0.3\n", encoding="utf-8")
        (root / "governance" / "framework.lock.json").write_text(
            json.dumps({"framework_repo": framework_repo, "adopted_commit": adopted_commit}),
            encoding="utf-8",
        )
        return temp, root, framework

    def fake_git(
        self,
        *,
        dirty: str = "",
        framework_head: str = "framework-head",
        verify_failure: bool = False,
    ):
        def call(repo: Path, *arguments: str) -> str:
            if arguments == ("status", "--porcelain", "--untracked-files=all"):
                return dirty
            if arguments == ("rev-parse", "--show-toplevel"):
                return str(repo)
            if arguments == ("rev-parse", "HEAD"):
                return framework_head if repo.name == "ai-governance-framework" else "parent-head"
            if arguments[:4] == ("config", "--file", ".gitmodules", "--get"):
                return CANONICAL_URL
            if arguments[:2] == ("bundle", "create"):
                Path(arguments[2]).write_bytes(b"git bundle")
                return ""
            if arguments[:2] == ("bundle", "verify"):
                if verify_failure:
                    raise bundle.BundleError("bundle verification failed")
                return ""
            raise AssertionError(f"unexpected git call: {repo} {arguments}")

        return call

    def fake_pip(self, command: list[str], *, cwd: Path | None = None) -> str:
        self.assertEqual(sys.executable, command[0])
        self.assertEqual(["-m", "pip", "download"], command[1:4])
        destination = Path(command[command.index("--dest") + 1])
        (destination / "dependency.whl").write_bytes(b"offline dependency")
        return ""

    def test_dirty_parent_is_rejected_before_output_creation(self) -> None:
        temp, root, framework = self.make_workspace()
        self.addCleanup(temp.cleanup)
        output = Path(temp.name) / "package"
        with patch.object(bundle, "git", self.fake_git(dirty=" M tracked")):
            with self.assertRaisesRegex(bundle.BundleError, "parent repo worktree is dirty"):
                bundle.create_bundle(root, output)
        self.assertFalse(output.exists())

    def test_lock_commit_mismatch_is_rejected(self) -> None:
        temp, root, framework = self.make_workspace(adopted_commit="wrong")
        self.addCleanup(temp.cleanup)
        output = Path(temp.name) / "package"
        with patch.object(bundle, "git", self.fake_git()):
            with self.assertRaisesRegex(bundle.BundleError, "lock does not match"):
                bundle.create_bundle(root, output)
        self.assertFalse(output.exists())

    def test_lock_framework_url_mismatch_is_rejected(self) -> None:
        temp, root, framework = self.make_workspace(framework_repo="https://example.invalid/wrong.git")
        self.addCleanup(temp.cleanup)
        output = Path(temp.name) / "package"
        with patch.object(bundle, "git", self.fake_git()):
            with self.assertRaisesRegex(bundle.BundleError, "URL does not match lock"):
                bundle.create_bundle(root, output)
        self.assertFalse(output.exists())

    def test_pip_failure_removes_partial_output(self) -> None:
        temp, root, framework = self.make_workspace()
        self.addCleanup(temp.cleanup)
        output = Path(temp.name) / "package"
        with patch.object(bundle, "git", self.fake_git()), patch.object(
            bundle, "run", side_effect=bundle.BundleError("pip failed")
        ):
            with self.assertRaisesRegex(bundle.BundleError, "pip failed"):
                bundle.create_bundle(root, output)
        self.assertFalse(output.exists())

    def test_bundle_verify_failure_removes_partial_output(self) -> None:
        temp, root, framework = self.make_workspace()
        self.addCleanup(temp.cleanup)
        output = Path(temp.name) / "package"
        with patch.object(bundle, "git", self.fake_git(verify_failure=True)):
            with self.assertRaisesRegex(bundle.BundleError, "bundle verification failed"):
                bundle.create_bundle(root, output)
        self.assertFalse(output.exists())

    def test_successful_bundle_orchestration_writes_verified_manifest(self) -> None:
        temp, root, framework = self.make_workspace()
        self.addCleanup(temp.cleanup)
        output = Path(temp.name) / "package"
        with patch.object(bundle, "git", self.fake_git()), patch.object(bundle, "run", self.fake_pip):
            bundle.create_bundle(root, output)
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("parent-head", manifest["parent_repo_head"])
        self.assertEqual("framework-head", manifest["framework_head"])
        self.assertEqual(CANONICAL_URL, manifest["framework_canonical_url"])
        self.assertTrue((output / "spec-reference-kit.bundle").is_file())
        self.assertTrue((output / "ai-governance-framework.bundle").is_file())

    def test_manifest_records_relative_file_hashes_and_sizes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            payload = output / "wheelhouse" / "dependency.whl"
            payload.parent.mkdir()
            payload.write_bytes(b"offline dependency")

            write_manifest(
                output,
                {
                    "parent_repo_head": "parent",
                    "framework_head": "framework",
                    "source_vault_included": False,
                },
            )
            write_manifest(
                output,
                {
                    "parent_repo_head": "parent",
                    "framework_head": "framework",
                    "source_vault_included": False,
                },
            )

            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("spec-reference-kit-disconnected-bundle.v1", manifest["format"])
            self.assertEqual(
                [
                    {
                        "path": "wheelhouse/dependency.whl",
                        "size": len(b"offline dependency"),
                        "sha256": hashlib.sha256(b"offline dependency").hexdigest(),
                    }
                ],
                manifest["files"],
            )
            self.assertNotIn("manifest.json", [item["path"] for item in manifest["files"]])
            self.assertNotIn("SHA256SUMS", [item["path"] for item in manifest["files"]])
            manifest_paths = {item["path"] for item in manifest["files"]}
            sums_paths = {
                line.split("  ", 1)[1]
                for line in (output / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
                if line
            }
            self.assertEqual(manifest_paths, sums_paths)
            self.assertEqual(
                f"{hashlib.sha256(b'offline dependency').hexdigest()}  wheelhouse/dependency.whl\n",
                (output / "SHA256SUMS").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()