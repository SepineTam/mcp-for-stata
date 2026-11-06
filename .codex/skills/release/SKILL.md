---
name: release
description: Prepare or publish a Stata-MCP version from master, including lint, version metadata, and GitHub Release notes. Use for release preparation, patch releases, or publishing an approved version.
---

# Stata-MCP Release

Start with the [release runbook](references/runbook.md). Go to the section for the current task to find the commands, expected results, and troubleshooting steps.

1. **Confirm the release scope.** From the repository root, inspect the branch, working tree, and changes since the previous stable release. Base the scope on the commit that will ship from `master`. Preserve unrelated uncommitted work. Keep security patches focused on the fixes they ship and leave later features on their branches. Follow the user's authorization for preparation, pushing, and public publication.
2. **Run lint on `master`.** Follow `.github/workflows/lint.yml`. Run `black src`, `black --check src`, then `flake8 src --extend-ignore=E501,W291,E203`. If Black would reformat many unrelated files, reproduce the CI sequence in a temporary copy and bring back only fixes relevant to the release. Report the working tree and temporary copy results separately. When authorized to commit, commit the lint fixes first in a separate commit.
3. **Prepare the version metadata.** Update `CHANGELOG.md` to reflect what ships and synchronize the package version in `pyproject.toml` with the server and PyPI package versions in `server.json`. When authorized, commit these three files together. Use `tests/test_release_metadata.py` to check consistency and select existing tests based on the changes.
4. **Draft release notes for review.** Save them at `releases/v-<major>-<minor>-<patch>.md` in the repository root, for example `releases/v-1-25-3.md`. Follow the [template](templates/release-notes.md) and recent stable releases. Describe user-visible changes, upgrade implications, and relevant settings. Git ignores this directory. Use the draft as the GitHub Release body. If local examples are missing, retrieve recent stable release bodies from GitHub in publication order, exclude drafts and prereleases, and preserve existing files.
5. **Push and publish.** Check which commits will be pushed and tell the user. Once the user approves the notes and authorizes publication, confirm that remote `master` contains the target commit and check for an existing tag or Release. Create the Release with tag `v<major>.<minor>.<patch>` pointing to the confirmed commit and pass the reviewed notes with `--notes-file`. If the version already exists, check its status before proceeding.

Publishing the GitHub Release triggers `.github/workflows/python-package.yml` for PyPI and the MCP Registry and `.github/workflows/release-binaries.yml` for platform binaries. Report the observed status of each separately.

## Reference Files

| Name | Location | Description |
|:---|:---|:---|
| Release Runbook | `references/runbook.md` | Steps and commands for preparing, pushing, publishing, and tracking a release |
| Release Notes Template | `templates/release-notes.md` | Scaffold for drafting release notes |

---
