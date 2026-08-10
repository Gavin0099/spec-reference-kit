# Disconnected internal adoption

## What this feature does

This kit turns a bounded claim from a controlled specification into a
reviewable reference lookup. It does not copy a specification into Git or let
an AI answer become canonical on its own.

The data path is:

1. A raw document stays in a read-only Source Vault outside Git.
2. The source registry records the document identity, scope, revision, locator,
  and SHA-256 fingerprint.
3. An extraction receipt records exactly which source surface was read.
4. An AI or engineer writes a proposal under `proposals/`.
5. A domain reviewer checks the source, claim scope, and exclusions, then writes
  a human review receipt.
6. `scripts/promote_entry.py` accepts the proposal only when all fingerprints
  and review fields match.
7. The promoted entry becomes canonical YAML under `tables/`; the manifest and
  Markdown are generated views of that YAML.

The result is useful for bounded lookups such as register address, bit range,
encoding, product scope, and silicon revision. It is deliberately not a
runtime behavior oracle, firmware-support database, certification record, or
customer-specific override system.

## Three different checks

Keep these outcomes separate:

| Check | What it proves | What it does not prove |
| --- | --- | --- |
| Disconnected package smoke | Git bundles, submodule bootstrap, offline dependencies, hashes, and repository startup work in an isolated environment. | That the internal Source Vault or real product data is available. |
| Synthetic scale smoke | The proposal, review-receipt, promotion, validation, and generation path handles 20 entries using fictional fixtures. | Extraction accuracy, reviewer time, or domain approval. |
| Real internal pilot | A real bounded source and domain review process produce approved entries with measured quality and review cost. | Runtime firmware behavior, certification, or customer acceptance. |

The public repository currently contains only the first two checks. The real
pilot must run in a private internal repository with the Source Vault and
reviewer authority available.

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

## Real pilot entry gate

Do not start the real pilot until every item below is available:

- an approved read-only Source Vault artifact;
- a source registry entry with a matching SHA-256;
- stable section, page, and table locators;
- extraction receipts for every proposed claim;
- a named domain reviewer with authority for the source scope;
- human review receipts with matching proposal fingerprints;
- an internal repository or transfer location that does not expose raw source
  documents in this public template.

## Real pilot procedure

1. Register one authoritative source and its SHA-256.
2. Select one low-ambiguity `register_bit` table first.
3. Extract 20–50 entries with stable page/section/table locators.
4. Let AI or an engineer create proposals only.
5. Have a domain reviewer issue review receipts.
6. Promote through the CLI and generate the approved views.
7. Record false extraction rate, median review time, rejected fingerprint
  count, and revision/supersedence handling.
8. Review the results before adding another entry type.

The current template cannot perform steps 1, 3, or 5 for real data because it
does not contain an internal Source Vault or a domain reviewer. Its synthetic
fixtures are useful for process rehearsal only.

Do not start with a full-spec vector database. That creates fast retrieval
before authority, scope, and supersedence are controlled.

