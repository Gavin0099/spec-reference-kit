# Tech Stack

## Repo Facts

- Runtime: Python 3.9+; core tooling must run without network access.
- Structured truth: YAML files under `sources/`, `proposals/`, `evidence/`,
  `tables/`, and `exports/`.
- Generated views: Markdown under `specs/generated/`; generated views are not
  independent authority.
- Governance dependency: `ai-governance-framework` git submodule pinned by the
  parent repository.
- Source boundary: raw PDF/Word/Excel specifications stay in an external,
  read-only Source Vault and must not be committed.
