# Release process

Nothing is built or deployed from this repository: a release is a Git tag
that callers reference from their `uses:` line.

- **Version.** SemVer `vX.Y.Z`. A change that can fail or change a caller's
  job without a change on the caller's side (a new failing check, a removed
  or renamed input, output or secret, wider permissions) is a major version.
- **Who and when.** The owner, or an agent the owner asks, after the
  release's changes are merged to `main` and the last `Validate CI
  Templates` run on `main` passed.
- **Steps.**
  1. In a pull request, rename `## [Unreleased]` in `CHANGELOG.md` to
     `## [X.Y.Z] - <date>` and add a new empty `## [Unreleased]` above it.
  2. After the merge, tag that commit and publish a GitHub Release with the
     section as notes:
     `gh release create vX.Y.Z --target <sha> --title vX.Y.Z --notes-file <section>`.
  3. Major tag: for a minor or patch release, move the major tag (`v1`)
     to the same commit (`git tag -f v1 <sha> && git push -f origin v1`);
     for a new major version, create its major tag (`git tag v2 <sha> &&
     git push origin v2`) and leave the old one where it is.
- **Callers** pin `vX.Y.Z` or its commit SHA (`docs/action-pinning.md`);
  the major tag is a convenience for non-sensitive workflows.
