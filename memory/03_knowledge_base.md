# Knowledge Base

## Gotchas

- Copy-based `adopt_governance.py` output is an audit surface only. Add the
  framework as a registered submodule before adoption when runtime-capable
  governance is intended.
- F-7 refuses a consuming repo with pre-existing staged files. Commit or unstage
  the bounded prior scope before rerunning; do not bypass the guard.
- `hook_install_validator` checked hook contents but did not detect missing Unix
  executable bits in this environment. A real commit exposed the gap; verify an
  actual trigger instead of treating file presence as execution evidence.
- PyYAML's default loader accepts duplicate mapping keys with last-value-wins
  behavior. Governed specification data uses a strict loader that rejects them.
