# F001 — Plan

## Applicable standards

- `.agents/core/standards/ci-cd.md` — shared pipeline ownership and validation.
- `.agents/core/standards/testing.md` — behavior and regression coverage.
- `.agents/core/standards/security.md` — external checkout and permissions.
- `.agents/core/standards/documentation.md` — consumer-facing behavior.
- `.agents/core/archetypes/devops-infra/` — pipeline review.

## Checklist

- [ ] Obtain review of this feature folder before implementation.
- [ ] Add failing tests for clean, core, marker file, current/vendor/retired skill, unrelated skill, combined findings, source failure, and all workflow integrations.
- [ ] Implement the shared warning check and pin the upstream source; ensure no copied skill list is maintained here.
- [ ] Integrate the check into each reusable workflow against the caller checkout and enable tests in repository CI.
- [ ] Update architecture and CI documentation with warning semantics, source and local gates.
- [ ] Run tests and local gates, perform DevOps review, change audit, docs sync, and release-readiness checks.

## Gates

Run the existing YAML parsing gate in `docs/ci-cd.md` and the new unit test command once added.

## Docs impact

- `docs/architecture.md` — checkout boundaries and pinned upstream source.
- `docs/ci-cd.md` — warning semantics and test commands.

## Next step

Obtain feature-plan review and approval.
