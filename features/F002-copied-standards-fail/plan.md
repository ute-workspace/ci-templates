# F002 — Plan

## Applicable standards

- agent-standards `test-strategy` — behaviour and regression coverage.
- agent-standards `devops-review` — shared pipeline behaviour change for callers on a mutable ref.
- agent-standards `docs-sync` — consumer-facing behaviour.

## Checklist

- [x] Script: `::error` per finding, exit 1; "not checked" path unchanged.
- [x] Embed the body in all five reusable workflows; remove `continue-on-error` from the check step.
- [x] Tests updated; unreadable skills directory case added.
- [x] `docs/architecture.md`, `docs/ci-cd.md`, `AGENTS.md`.
- [ ] Change audit, then mark the PR ready.

## Gates

`python3 -m unittest discover -s tests -v` and the YAML parsing snippet in `docs/ci-cd.md`.

## Risks

- Callers on `@main` start failing at once if they still carry copied standards; callers pinned to a tag or SHA are unaffected until they bump.

## Next step

Change audit.
