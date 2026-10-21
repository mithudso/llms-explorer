# Canonical Claude companion snapshot

These two assets were copied verbatim from `~/.claude/skills/concept-family-explorer`
on 2026-10-20. The repository Claude skill references them but its source directory
omits them. Keep the snapshot tracked so a clean checkout can reproduce the Codex
sync without a populated user home. The generated sync manifest records each
source and rendered SHA256.

Repository `.claude/skills` files take precedence. An explicit
`--canonical-root ~/.claude/skills` supplies or refreshes missing companions for
one sync; update this pinned snapshot when adopting those changes permanently.
The generator preserves the helper's shared catalogue paths and applies the same
Codex documentation overlay to its reference as to repository sources.
