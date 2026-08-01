# PLAN.md
<!-- governance-baseline: overridable -->
<!-- baseline_version: 1.0.0 -->

> **最後更新**: 2026-08-01
> **Owner**: Gavin0099
> **Freshness**: Sprint (7d)

---

## Current Phase

<!-- Required: fill in current phase ID and description -->

- [x] Phase A: Governance bootstrap and synthetic vertical slice
- [ ] Phase B: Disconnected internal pilot with 20–50 reviewed entries

## Active Sprint

<!-- Required: list current sprint tasks -->

- [x] Add the canonical AI Governance Framework as a pinned submodule.
- [x] Adopt the repo-owned governance baseline and classify promotion paths as high risk.
- [x] Complete the governed F-7 onboarding surfaces and evidence.
- [x] Deliver one synthetic source-to-approved-reference vertical slice.

## Backlog

<!-- Required: prioritized items not yet started -->

- P1: Package parent repo and framework bundles for disconnected import.
- P2: Add a second entry type only after the register-bit pilot exposes a real gap.
- P3: Add VitePress, MCP, or RAG only after the approved surface is useful without them.

## Decision Log

<!-- Optional but recommended: record architecture or governance decisions with dates -->

- 2026-08-01: Use a framework submodule instead of copied governance files so
  provenance and managed updates remain inspectable.
- 2026-08-01: Keep raw source artifacts outside Git; the repository stores only
  source identities, locators, hashes, bounded extracts, and approved claims.
- 2026-08-01: v0.1 is one synthetic register-bit vertical slice. YAML remains
  canonical; Markdown and the manifest are deterministic projections.
- 2026-08-01: Reject duplicate YAML keys rather than accepting PyYAML's default
  last-value-wins behavior; silent overwrite is incompatible with reviewable truth.

## Known Risks

<!-- Optional: track identified risks and mitigation status -->

- Promotion could launder an AI proposal into normative-looking data. Mitigation:
  require a human review receipt and matching source/proposal fingerprints.
- An offline clone can initialize the parent repo but fail on the submodule.
  Mitigation: document a two-bundle or internal-mirror import path before v0.1 release.
- Schema breadth can displace product utility. Mitigation: stop after one entry
  type until a real internal pilot identifies the next required type.
- Human review receipts are attestations, not cryptographic identity proof.
  Mitigation: rely on internal Git identity/branch protection for the pilot and
  evaluate signed receipts only if a real impersonation or audit gap is observed.
