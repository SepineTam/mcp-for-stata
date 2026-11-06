# Stata-MCP Release Runbook

Run commands from the repository root. The GitHub repository is `SepineTam/mcp-for-stata` and the release branch is `master`.

## 1. Confirm the release scope

```bash
git status --short --branch
git log -8 --oneline --decorate
gh release list --repo SepineTam/mcp-for-stata --limit 15
```

Start with the stage the user requested. Go to section 4 to push commits, section 5 to publish a reviewed version, or section 6 to check publication results.

When preparing a version, set `previous_tag` to the previous stable release tag. If it is missing locally, fetch it with `git fetch origin "refs/tags/$previous_tag:refs/tags/$previous_tag"`. Review what will ship from `master`.

```bash
git log --oneline "$previous_tag"..master
git diff --stat "$previous_tag"..master
```

If the user requests a merge, inspect the commits on both branches. If `master` is an ancestor of the fix branch, switch to `master` and run `git merge --ff-only <fix-branch>`. If the branches have diverged, confirm the merge scope first.

## 2. Run lint on master

```bash
uvx black --check src
uvx flake8 src --extend-ignore=E501,W291,E203
```

If Black would reformat many unrelated files, fix the issues relevant to this release and reproduce the CI sequence in a temporary copy.

```bash
lint_dir=$(mktemp -d) &&
cp -R src "$lint_dir/src" &&
(
  cd "$lint_dir" &&
  uvx black src &&
  uvx black --check src &&
  uvx flake8 src --extend-ignore=E501,W291,E203
)
```

Report the working tree and temporary copy results separately. When authorized to commit, commit the lint fixes first with `git commit --only -m 'chore(lint): ...' -- <lint-fix-files>`.

## 3. Prepare version metadata and release notes

Update `CHANGELOG.md`. Set the same version in `pyproject.toml`, at the top level of `server.json`, and in its PyPI package entry. When authorized, commit the three files together.

```bash
uv run pytest tests/test_release_metadata.py -q
git diff --check
git diff -- CHANGELOG.md pyproject.toml server.json
```

Use the [template](../templates/release-notes.md) to write a local draft. For version `1.25.3`, use `releases/v-1-25-3.md` and tag `v1.25.3`. Use `Fix` for fixes and `Feat` for features. Share the draft path and target commit with the user for review.

To replenish local examples, select the 13 most recent stable GitHub Releases by publication time, excluding drafts and prereleases. Retrieve the original body of each release and save it under `releases/` using hyphenated version names. Compare existing files before writing.

```bash
gh release view v1.25.2 --repo SepineTam/mcp-for-stata --json body --jq .body
```

If the user asks for local packages, run `uv build --out-dir <temporary-output-directory>`. Expect a wheel and a source distribution. If an offline build cannot find `uv-build` or an older uv fails during extraction, check the build requirements in `pyproject.toml` and the output of `uv --version`, then retry with a compatible version.

## 4. Push confirmed commits

Before pushing, run `git log --oneline origin/master..master` to see what will go to remote `master`. For a fix branch, likewise check the difference between the local and remote branch. Use the destination the user requested, either `git push origin master` or `git push -u origin <fix-branch>`.

## 5. Create the GitHub Release

Once the user has reviewed the notes and authorized publication, set `tag` to the release tag. Check the remote commit, tag, and existing Release.

```bash
git ls-remote origin refs/heads/master "refs/tags/$tag"
gh release view "$tag" --repo SepineTam/mcp-for-stata
```

If the tag exists, confirm that it resolves to the intended commit, including the dereferenced commit for an annotated tag. If a Release exists, check whether it is a draft or already published. Resolve authentication or connection errors before proceeding.

For a new Release, set `release_commit` to the confirmed full commit hash and `notes_file` to the path of the reviewed Markdown file.

```bash
gh release create "$tag" --repo SepineTam/mcp-for-stata \
  --target "$release_commit" --title "Stata-MCP $tag" \
  --notes-file "$notes_file"
```

## 6. Track publication

```bash
gh release view "$tag" --repo SepineTam/mcp-for-stata --json url,isDraft,assets
gh run list --repo SepineTam/mcp-for-stata --event release --limit 10
```

Find the runs for the version and inspect their steps with `gh run view <run-id> --json status,conclusion,jobs,url`. The same workflow publishes to PyPI first and then to the MCP Registry. If PyPI succeeds and the Registry fails, check the failed step and the live version before choosing how to resume, so the package is uploaded only once. Check the Linux, macOS, and Windows binary builds separately and confirm their assets are attached to the Release.
