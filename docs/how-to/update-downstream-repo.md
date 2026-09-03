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

If you've modified any of the files, Copier will show any conflicting changes
for you to resolve.

## Automate updates with GitHub Actions

Downstream repositories can set up automated Copier updates using the callable
workflow provided by this template. The workflow checks for template updates,
runs `copier update`, and opens a pull request with the changes.

### Set up the workflow

Add a workflow file to your downstream repository (e.g.,
`.github/workflows/sync-docs-template.yml`):

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
trigger so you can start the update manually.

## Update project-specific values

If you need to change a project-specific value (for example, a new Discourse URL):

1. Update the value in `.copier-answers.yml`.
2. Run `copier update` to re-render templated files with the new value.
3. Review and commit the changes.
