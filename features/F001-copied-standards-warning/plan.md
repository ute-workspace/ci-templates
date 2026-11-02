# F001 — Plan

## Applicable standards

- `.agents/core/standards/ci-cd.md` — shared pipeline ownership and validation.
- `.agents/core/standards/testing.md` — behavior and regression coverage.
- `.agents/core/standards/security.md` — external checkout and permissions.
- `.agents/core/standards/documentation.md` — consumer-facing behavior.
- `.agents/core/archetypes/devops-infra/` — pipeline review.

## Checklist

- [x] Plan approved (UND-24 plan document).
- [x] Shared warning check `scripts/check-copied-standards.sh` (fixed paths only).
- [x] Tests for clean, individual, multiple, both-skill-directory, missing-checkout cases and all five workflow integrations.
- [x] Embed the check in each reusable workflow against the caller checkout; run tests in `validate.yml`.
- [x] Update `docs/architecture.md` and `docs/ci-cd.md`.
- [ ] Independent Reviewer and Security reviews of the draft PR.
- [ ] Change audit, then mark the PR ready.

## Gates

`python3 -m unittest discover -s tests -v` and the YAML parsing snippet in `docs/ci-cd.md`.

## Docs impact

- `docs/architecture.md` — check, caller checkout boundary, warning semantics.
- `docs/ci-cd.md` — tests job and local gates.

## Next step

Independent Reviewer and Security reviews of the draft PR.
