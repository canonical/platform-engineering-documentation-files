# How to update a downstream repository

When this repository is updated, downstream repositories should pull in the changes
to remain in sync.

## Perform a manual update

Manually update the files from the root of your downstream repository using:

```bash
copier update
```

Copier will update all static files, and templated files are re-rendered
with your existing answers.

Copier will merge template changes into your repository, preserving your
project-specific values from `.copier-answers.yml`. Review the diff, resolve
any conflicts, and commit.

If you've modified any of the managed files, Copier may report merge conflicts
for you to resolve. See [Resolve merge conflicts](#resolve-merge-conflicts) below.

## Automate updates with GitHub Actions

Downstream repositories can set up automated Copier updates using the callable
workflow provided by this template. The workflow checks for template updates,
runs `copier update`, and opens a pull request with the changes.

Add a workflow file to your downstream repository (e.g.,
`.github/workflows/sync_docs_template.yaml`):

```yaml
name: Sync with platform-engineering-documentation-files

on:
  schedule:
    - cron: "0 6 * * 1" # Every Monday at 6 AM UTC
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  sync:
    uses: canonical/platform-engineering-documentation-files/.github/workflows/copier-update.yml@main
    secrets:
      token: ${{ secrets.GITHUB_TOKEN }}
```

The workflow checks if this repository has new commits since the last update,
running `copier update` if there are changes and opening a PR with the diff.
If `copier update` produces merge conflicts, 
they are left inline for you to review and resolve before merging the changes.

We recommend running the workflow on a schedule and leaving a `workflow_dispatch`
trigger so you can start the update manually if needed.

## Resolve merge conflicts

`copier update` re-applies your repository's changes on top of the re-rendered
template as a three-way merge. If you modified a managed file, merge conflicts can arise if the template
affects the modified area. Copier does not resolve these for you:
it writes both versions into the file between conflict markers and leaves them for
you to resolve.

For example, a `docs/conf.py` conflict looks like:

```python
<<<<<<< before updating
intersphinx_mapping = {
    "juju": ("https://canonical.com/juju/docs/juju-cli/3.6/", None),
}
=======
intersphinx_mapping = {
    "juju": ("https://canonical.com/juju/docs/juju-cli/3.6/", None),
    "ops": ("https://documentation.ubuntu.com/ops/latest/", None),
}
>>>>>>> after updating
```

The section above `=======` is your current content; the section below it is the
incoming template version. While the markers are present, a file that is executed
at build time (such as `conf.py`) is invalid, so the documentation build fails until
you resolve them.

To resolve a conflict:

1. Open each file that contains `<<<<<<<`, `=======`, and `>>>>>>>` markers.
2. Edit the region to the result you want — keeping your changes, the template's
   changes, or a combination — and delete all three marker lines.
3. Rebuild the documentation to confirm the result is valid:

   ```bash
   make html
   ```

4. Commit the resolved files.

When the update runs through the GitHub Actions workflow, perform these same steps
on the pull request branch before merging it.

## Update project-specific values

If you need to change a project-specific value, pass the new value
in `copier update` using the `--data` flag. For example, update
the `discourse` value using:

```
copier update --data discourse="https://discourse.example.com"
```

Or run `copier update` with no arguments and re-answer the questionnaire;
your previous answers are offered as defaults. Review and commit the result.

> See also: [Never change the answers file manually - copier](https://copier.readthedocs.io/en/stable/updating/#never-change-the-answers-file-manually)