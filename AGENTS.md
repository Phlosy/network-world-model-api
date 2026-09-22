# Network World Model API Agent Guidance

This repository is the language-independent OpenAPI source of truth for Network World Model and publishes matching Go and Python libraries from one release commit. Generated files are committed; do not edit generated Go or Python sources by hand.

## Contract Workflow

1. Edit the OpenAPI contract in `contracts/openapi/network-world-state.openapi.json`.
2. Run `make lint` to ensure OpenAPI 3.0.3 compliance with Redocly.
3. Run `make generate` to regenerate both Go and Python sources.
4. Run `make test` to execute all unit tests.
5. Run `make verify` and `git diff --check` before committing.

## Release Workflow

All language artifacts share the plain `X.Y.Z` value in `VERSION`. Use the repository-owned release script rather than editing version declarations or creating release tags individually:

```sh
scripts/release.sh set-version X.Y.Z
```

This updates `VERSION`, the Python package metadata, and `__init__.py`. Review and commit those changes with the release before tagging:

```sh
git commit -am "chore(release): prepare release X.Y.Z"
```

After the release commit is on `main`, with a clean worktree, create both local annotated tags:

```sh
scripts/release.sh tag X.Y.Z
```

The script creates `vX.Y.Z` for the repository and Python release, and `go/vX.Y.Z` for the Go module in the `go/` subdirectory. Both tags point to the same commit.

Push the reviewed commit and tags explicitly:

```sh
git push origin main --tags
```
