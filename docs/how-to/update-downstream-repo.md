# How to update a downstream repository

When this template repository is updated (new tooling, bug fixes, new Sphinx
extensions), downstream repos can pull in the changes.

Manually update the files from the root of your downstream repository using:

```bash
copier update
```

Copier will merge template changes into your repository, preserving your
project-specific values from `.copier-answers.yml`. Review the diff, resolve
any conflicts, and commit.

### What Copier updates

- All static files (Makefile, requirements, `_dev/`, `_templates/`, workflows, and so on)
- Templated files are re-rendered with your existing answers

### What Copier preserves

- Your project-specific answers in `.copier-answers.yml`
- Any files you've modified locally that conflict with template changes (Copier will
  show conflicts for you to resolve)

## Automated updates with GitHub Actions

Downstream repositories can set up automated Copier updates using the callable
workflow provided by this template. The workflow checks for template updates,
runs `copier update`, and opens a pull request with the changes.

### Setup

Add a workflow file to your downstream repository (e.g.,
`.github/workflows/sync-docs-template.yml`):

```yaml
name: Sync with platform-engineering-documentation-files

on:
  schedule:
    - cron: "0 6 * * 1" # Every Monday at 6 AM UTC
  workflow_dispatch: # Manual trigger

permissions:
  contents: write
  pull-requests: write

jobs:
  sync:
    uses: canonical/platform-engineering-documentation-files/.github/workflows/copier-update.yml@main
    secrets:
      token: ${{ secrets.GITHUB_TOKEN }}
```

### How it works

1. The workflow runs on the schedule you configure (weekly recommended) or on demand.
2. It checks if the template has new commits since the last update.
3. If there are changes, it runs `copier update` and opens a PR with the diff.
4. You review and merge the PR like any other change.

## Troubleshooting

### Merge conflicts

If `copier update` produces merge conflicts, Copier will mark them in the
affected files. Resolve them manually, then commit. Common causes:

- You've made local modifications to a file that the template also changed.
- A templated file was edited directly instead of updating `.copier-answers.yml`
  and re-running `copier update`.

### Update appears to do nothing

If `copier update` reports no changes:

- Confirm the template has new commits since your last update.
- Check that your `.copier-answers.yml` `_commit` field references an older
  template commit.
- Run `copier update --vcs-ref=HEAD` to force an update to the latest template
  commit.

### Changing project values

If you need to change a project-specific value (for example, a new Discourse URL):

1. Update the value in `.copier-answers.yml`.
2. Run `copier update` to re-render templated files with the new value.
3. Review and commit the changes.
