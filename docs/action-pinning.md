# Action pinning policy

Every `uses:` of a third-party action in this repository's workflows is
pinned to the full commit SHA of a released tag, with that tag as a trailing
comment:

```yaml
uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
```

A caller of a reusable workflow cannot change the actions inside it, so the
pins are made here, not in consumer repositories. Before pinning a new SHA,
check that the tag's commit is on the action's default branch.

Renovate (`renovate.json`, preset `helpers:pinGitHubActionDigests`) proposes
updates of the SHA and its comment; a major version update is reviewed and
released as its own change.

Callers pin this repository the same way: a release tag (`vX.Y.Z`) or a
commit SHA. A moving major tag (`v1`) is a convenience for non-sensitive
workflows only. Do not use an unreviewed pull request branch or a mutable
tag in protected deployment workflows.
