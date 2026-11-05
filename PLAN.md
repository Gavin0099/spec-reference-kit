# PLAN.md
<!-- governance-baseline: overridable -->
<!-- baseline_version: 1.0.0 -->

> **最後更新**: 2026-11-05
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
- [x] Package parent and framework Git bundles with offline dependencies and hashes.
- [x] Replay the disconnected bundle import in a short-path isolated smoke environment; evidence: `artifacts/evidence/test-results/phase-b-disconnected-import-smoke.json`.
- [x] Run a bounded 20-entry synthetic register-bit promotion/generation smoke; evidence: `artifacts/evidence/test-results/phase-b-synthetic-register-pilot.json`.

## Backlog

<!-- Required: prioritized items not yet started -->

- P1: Obtain an approved read-only internal Source Vault artifact, fingerprint it, and run the real 20-50 entry register-bit pilot with a domain reviewer.
- P2: Add a second entry type only after the real register-bit pilot exposes a documented gap.
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
- 2026-11-05: Adopt framework 859445c2 through F-7 (pinned target) to retire the
  legacy Copilot Stop -> session_end hook, which ran the session-end closeout
  after every agent turn; sessionStart/sessionEnd stay in ai-governance-copilot.json.

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
- The local disconnected smoke and synthetic scale pilot do not establish a real
  internal pilot. Mitigation: keep real Source Vault content outside Git and
  require domain review before any production-facing promotion.
