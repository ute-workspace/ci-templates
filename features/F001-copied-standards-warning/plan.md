# F001 — Plan

## Applicable standards

- agent-standards `test-strategy` — behavior and regression coverage.
- agent-standards `security-review` — external checkout and permissions.
- agent-standards `docs-sync` — consumer-facing behavior.
- agent-standards `devops-review` — shared pipeline ownership, validation and review.

## Checklist

- [x] Plan approved (UND-24 plan document).
- [x] Shared warning check `scripts/check-copied-standards.sh` (fixed paths only).
- [x] Tests for clean, individual, multiple, both-skill-directory, missing-checkout cases and all five workflow integrations.
- [x] Embed the check in each reusable workflow against the caller checkout; run tests in `validate.yml`.
- [x] Update `docs/architecture.md` and `docs/ci-cd.md`.
- [x] Independent Reviewer and Security reviews of the draft PR (UND-57, UND-58).
- [x] Review fixes: checkout outcome, summary escaping, symlink and non-directory skills paths (UND-66).
- [x] Re-reviews (UND-67, UND-68).
- [x] Review fixes: sparse checkout of symlinked parents, skill-name skip, display disposition (UND-72).
- [ ] Re-review of the UND-72 fixes.
- [ ] Change audit, then mark the PR ready.

## Gates

`python3 -m unittest discover -s tests -v` and the YAML parsing snippet in `docs/ci-cd.md`.

## Docs impact

- `docs/architecture.md` — check, caller checkout boundary, warning semantics.
- `docs/ci-cd.md` — tests job and local gates.

## Next step

Re-review of the UND-72 fixes, then change audit.
