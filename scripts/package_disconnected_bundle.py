#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


class BundleError(RuntimeError):
    pass


def run(command: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise BundleError(f"command failed ({result.returncode}): {' '.join(command)}\n{detail}")
    return result.stdout.strip()


def git(repo: Path, *arguments: str) -> str:
    return run(["git", "-C", str(repo), *arguments])


def git_root(repo: Path) -> Path:
    return Path(git(repo, "rev-parse", "--show-toplevel")).resolve()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_clean(repo: Path, label: str) -> None:
    status = git(repo, "status", "--porcelain", "--untracked-files=all")
    if status:
        raise BundleError(f"{label} worktree is dirty:\n{status}")


def framework_url(repo: Path) -> str:
    url = git(repo, "config", "--file", ".gitmodules", "--get", "submodule.ai-governance-framework.url")
    if not url:
        raise BundleError("framework URL is missing from .gitmodules")
    return url


def write_manifest(output: Path, metadata: dict[str, object]) -> None:
    files = sorted(
        path
        for path in output.rglob("*")
        if path.is_file() and path.name not in {"manifest.json", "SHA256SUMS"}
    )
    manifest = {
        "format": "spec-reference-kit-disconnected-bundle.v1",
        **metadata,
        "files": [
            {
                "path": path.relative_to(output).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in files
        ],
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "SHA256SUMS").write_text(
        "".join(f"{item['sha256']}  {item['path']}\n" for item in manifest["files"]),
        encoding="utf-8",
    )


def create_bundle(repo: Path, output: Path) -> None:
    framework = repo / "ai-governance-framework"
    lock_path = repo / "governance" / "framework.lock.json"
    requirements_path = repo / "requirements.txt"
    if not framework.is_dir():
        raise BundleError(f"framework submodule is missing: {framework}")
    if not lock_path.is_file():
        raise BundleError(f"framework lock is missing: {lock_path}")
    if not requirements_path.is_file():
        raise BundleError(f"requirements.txt is missing: {requirements_path}")

    require_clean(repo, "parent repo")
    try:
        framework_root = git_root(framework)
    except BundleError as exc:
        raise BundleError(f"framework submodule is not initialized: {framework}") from exc
    if framework_root != framework.resolve():
        raise BundleError(f"framework submodule is not initialized: {framework}")
    require_clean(framework, "framework submodule")
    parent_head = git(repo, "rev-parse", "HEAD")
    framework_head = git(framework, "rev-parse", "HEAD")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("adopted_commit") != framework_head:
        raise BundleError(
            "framework lock does not match submodule HEAD: "
            f"lock={lock.get('adopted_commit')} checkout={framework_head}"
        )
    canonical_url = framework_url(repo)
    if lock.get("framework_repo") != canonical_url:
        raise BundleError(
            "framework URL does not match lock: "
            f"gitmodules={canonical_url} lock={lock.get('framework_repo')}"
        )

    output_created = False
    try:
        output.mkdir(parents=True, exist_ok=False)
        output_created = True
        wheelhouse = output / "wheelhouse"
        wheelhouse.mkdir()
        parent_bundle = output / "spec-reference-kit.bundle"
        framework_bundle = output / "ai-governance-framework.bundle"
        git(repo, "bundle", "create", str(parent_bundle), "--all")
        git(framework, "bundle", "create", str(framework_bundle), "--all")
        git(repo, "bundle", "verify", str(parent_bundle))
        git(framework, "bundle", "verify", str(framework_bundle))
        run(
            [
                sys.executable,
                "-m",
                "pip",
                "download",
                "--only-binary=:all:",
                "--dest",
                str(wheelhouse),
                "-r",
                str(requirements_path),
            ]
        )
        write_manifest(
            output,
            {
                "parent_repo_head": parent_head,
                "framework_head": framework_head,
                "framework_canonical_url": canonical_url,
                "requirements": "requirements.txt",
                "source_vault_included": False,
            },
        )
    except BaseException:
        if output_created:
            shutil.rmtree(output, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a verified disconnected import package for this repository."
    )
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        create_bundle(args.repo.resolve(), args.output.resolve())
    except (BundleError, OSError, json.JSONDecodeError) as exc:
        print(f"[disconnected-bundle] FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"[disconnected-bundle] PASS: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())