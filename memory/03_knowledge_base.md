# Knowledge Base

## Gotchas

- Copy-based `adopt_governance.py` output is an audit surface only. Add the
  framework as a registered submodule before adoption when runtime-capable
  governance is intended.
- F-7 refuses a consuming repo with pre-existing staged files. Commit or unstage
  the bounded prior scope before rerunning; do not bypass the guard.
