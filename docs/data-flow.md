# Data flow and claim boundaries

## Three physical layers

1. `spec-reference-kit`: public schemas, tools, synthetic fixtures, and
   governance integration.
2. Private content repository: internal registry, proposals, review receipts,
   canonical tables, and generated views.
3. Source Vault: raw controlled documents stored outside Git with read-only
   access and independent backup/retention controls.

The kit should be imported into a new private repository. It should not become a
single shared repository containing every product and customer.

## Authority is not review status

| Axis | Example | Meaning |
| --- | --- | --- |
| `authority.level` | `internal_normative` | What authority the cited source has |
| `review.status` | `proposed` | Whether this extracted claim has been approved |

An `internal_normative` proposal is not yet approved. An approved
`engineering_note` remains an engineering note and must not be promoted to a
normative requirement by wording.

## Promotion invariants

Promotion fails when any of these conditions is not met:

- source ID exists in the registry;
- proposal source fingerprint equals the registered artifact fingerprint;
- extraction receipt exists and matches source, locator, and extracted-surface
  fingerprints;
- proposal is still `proposed` and not self-marked eligible;
- review receipt is `approved`, declares a human reviewer, and matches the
  canonical proposal fingerprint;
- product/revision scope and verification exclusions are non-empty;
- entry ID is unique in the destination table.

These checks make accidental or inconsistent promotion visible. They are not a
security boundary against a malicious committer who can rewrite code, receipts,
and Git history.

