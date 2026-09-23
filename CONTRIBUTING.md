# Contributing

## Commit messages: Conventional Commits

This repo releases automatically with [semantic-release](https://semantic-release.gitbook.io/), which
derives the next version number and changelog entry from commit messages on `main`. Write commits in
[Conventional Commits](https://www.conventionalcommits.org/) form:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Common types and their release effect:

- `fix:` — patch release (bug fix)
- `feat:` — minor release (new feature)
- `feat!:` or a footer of `BREAKING CHANGE: ...` — major release
- `chore:`, `docs:`, `test:`, `refactor:`, `style:`, `ci:` — no release by default

On every push to `main`, the `Release` GitHub Actions workflow (`.github/workflows/release.yml`) runs
semantic-release, which:

1. Determines the next version from the commits since the last release.
2. Updates `CHANGELOG.md` and the `version` field in `pyproject.toml`.
3. Commits those files back to `main` and creates a GitHub release with generated notes.

No package is published to npm or PyPI by this workflow; it only manages versioning, changelog, and
GitHub releases.
