# Disconnected internal adoption

## Recommended topology

- Mirror `ai-governance-framework` into an internal Git server.
- Create one private reference repository per product family or authority
  boundary.
- Create separate overlay repositories for customer-specific requirements.
- Store source documents in a read-only Source Vault outside Git.

Do not put all customer overlays into one manifest or vector index. Access
control, supersedence, and leakage impact differ by customer.

## Transfer into a disconnected network

In the connected staging environment:

The repository provides a verified packaging entry point. Run it outside the
repository so the output directory cannot make the source worktree dirty:

```bash
python scripts/package_disconnected_bundle.py \
  --repo spec-reference-kit \
  --output ../spec-reference-kit-disconnected-v0.1
```

The command requires clean parent and framework worktrees, verifies that the
framework lock matches the checked-out submodule commit, creates and verifies
both Git bundles, downloads binary dependencies into `wheelhouse/`, and writes
`manifest.json` plus `SHA256SUMS`. The package never includes the external
Source Vault.

The equivalent individual commands are shown below for troubleshooting or a
reviewer who needs to inspect each transfer artifact separately:

```bash
git -C spec-reference-kit bundle create ../spec-reference-kit-v0.1.bundle --all
git -C ai-governance-framework bundle create ../ai-governance-framework.bundle --all
git -C spec-reference-kit bundle verify ../spec-reference-kit-v0.1.bundle
git -C ai-governance-framework bundle verify ../ai-governance-framework.bundle
python -m pip download --only-binary=:all: \
  --dest ../wheelhouse -r spec-reference-kit/requirements.txt
```

Move both bundles and the wheelhouse through the approved company transfer
process. Hash and scan the transfer package according to internal policy.

Inside the disconnected network:

```bash
git clone spec-reference-kit-v0.1.bundle internal-product-spec-reference
git clone --mirror ai-governance-framework.bundle /srv/git/ai-governance-framework.git
git -C internal-product-spec-reference config \
  url.file:///srv/git/ai-governance-framework.git.insteadOf \
  https://github.com/Gavin0099/ai-governance-framework.git
git -C internal-product-spec-reference submodule update --init --recursive
python -m pip install --no-index --find-links wheelhouse \
  -r internal-product-spec-reference/requirements.txt
```

An internal Git server is preferable to a workstation-only bare repo. The
`insteadOf` mapping above is a bootstrap option; a reviewed internal
`.gitmodules` URL is clearer for a long-lived private repository.

## First pilot

1. Register one authoritative source and its SHA-256.
2. Select one simple table such as register bits, command IDs, or error codes.
3. Extract 20–50 entries with stable page/section/table locators.
4. Let AI or an engineer create proposals only.
5. Have a domain reviewer issue review receipts.
6. Promote through the CLI and generate the approved views.
7. Measure false extraction, review time, and version-delta handling before
   adding another entry type.

Do not start with a full-spec vector database. That creates fast retrieval
before authority, scope, and supersedence are controlled.

