# Spec Reference Kit

`spec-reference-kit` is a confidentiality-safe template for turning controlled
specification sources into reviewable, structured reference data.

It is deliberately **not** a specification repository, raw-document RAG system,
or compliance authority. The public kit contains only synthetic demo data. Real
PDF, Word, Excel, customer, product, register, command, and firmware content must
remain in a private internal repository and an external read-only Source Vault.

## v0.1 vertical slice

```text
Source Vault + source registry
             ↓
     extraction receipt
             ↓
       AI/human proposal
             ↓
 schema + provenance validation
             ↓
       human review receipt
             ↓
      explicit promotion CLI
             ↓
 canonical YAML → manifest + Markdown
```

The checked-in example uses a fictional device and values. It demonstrates the
workflow; it is not a real internal, vendor, customer, USB-IF, firmware, or
silicon specification.

## Trust boundaries

- Raw sources live outside Git in a read-only Source Vault.
- AI-authored content may enter only `proposals/`.
- Canonical data lives in `tables/` and requires an approved human review
  receipt whose proposal and source fingerprints match.
- `authority.level` describes the source's authority. `review.status` describes
  whether this extracted claim was reviewed. They are separate axes.
- `approved` means only that the claim matches the cited source within its
  declared scope. It does not prove runtime behavior, firmware support, silicon
  correctness, certification, or customer acceptance.
- Generated Markdown is a view. Canonical YAML is the source of truth.

## Quick start

Requires Python 3.9+ and PyYAML. Once dependencies are present, all commands run
without network access.

```bash
python scripts/validate_repository.py --repo . --check-generated
python scripts/probe_fingerprint.py \
  --registry sources/source_registry.yaml \
  --vault-root tests/fixtures/vault
python -m unittest discover -s tests -v
```

To replay promotion without changing the checked-in canonical table:

```bash
tmp_dir="$(mktemp -d)"
cp tables/register_matrix.empty.yaml "$tmp_dir/register_matrix.yaml"
python scripts/promote_entry.py \
  --proposal proposals/register_map/demo_reg_0082_bit3.yaml \
  --review-receipt evidence/review_packets/REV-DEMO-0001.yaml \
  --table "$tmp_dir/register_matrix.yaml"
```

See [docs/internal-adoption.md](docs/internal-adoption.md) for the disconnected
internal workflow and [docs/data-flow.md](docs/data-flow.md) for the authority,
review, and promotion model.

## Current scope

Included in v0.1:

- source registry and fingerprint probe;
- extraction and human-review receipts;
- one `register_bit` proposal/canonical schema;
- fail-closed promotion checks;
- governed-surface manifest;
- deterministic Markdown generation;
- positive and negative pipeline tests;
- AI Governance Framework as a pinned submodule.

Not included:

- VitePress, MCP, RAG, or chat UI;
- arbitrary PDF/table extraction;
- timing diagrams, state machines, or cross-document inference;
- customer overlays;
- claims that the human reviewer identity is cryptographically authenticated.

