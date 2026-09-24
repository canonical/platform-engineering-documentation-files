---
name: phase-8-post-onboarding
description: "Phase 8 of the onboard-existing-docs skill. Provides post-onboarding guidance and cleanup instructions."
---

# Phase 8: Post-Onboarding Guidance

**Prerequisites:** Phase 7 (`phase-7-validate-commit`) must be complete. The build must succeed and changes must be committed.

---

## Instructions

### Step 1: Deliver post-onboarding guidance

Tell the user the following key points:

1. **`.copier-answers.yml` is the source of truth** — It records all project-specific values. **Do not edit it manually.** If you need to change a value (e.g., a new Discourse URL), update `.copier-answers.yml` and re-run `copier update`.

2. **Future template updates** — When this template repository is updated (new tooling, bug fixes, new Sphinx extensions), pull in the changes:
   ```bash
   copier update
   ```
   Copier will merge template changes into your repository, preserving your project-specific values. Review the diff, resolve any conflicts, and commit.

3. **Changing a project value** — To change a project value (e.g., a new Discourse URL, updated author name):
   - Edit `.copier-answers.yml` with the new value
   - Run `copier update` to re-render templated files
   - Review and commit the changes

4. **Clean up the backup** — The backup at `/tmp/docs-backup/` can be deleted once everything is confirmed working:
   ```bash
   rm -rf /tmp/docs-backup/
   ```

5. **`.licenserc.yaml` update** — If the repo had a `.licenserc.yaml`, `.copier-answers.yml` was added to its `paths-ignore` list during Phase 7. Verify this was done correctly.

### Step 2: Offer to set up automated Copier updates

Offer to create a GitHub Actions workflow that automatically checks for template
updates and opens PRs. This keeps the downstream repo in sync with the central
management solution without manual intervention.

Ask the user: "Would you like me to create a GitHub Actions workflow that
automatically runs `copier update` on a schedule and opens PRs when the template
changes?"

If the user agrees, create `.github/workflows/sync_docs_template.yml` with the
following content:

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

The workflow checks if the template repository has new commits since the last
update, runs `copier update` if there are changes, and opens a PR with the diff.
If `copier update` produces merge conflicts, they are left inline for the user
to review and resolve before merging.

### Step 3: Set up Read the Docs (if applicable)

If the project uses Read the Docs, remind the user to configure their project on Read the Docs to build from the repository. The generated `.readthedocs.yaml` is already configured.

### Step 4: Offer PR description guidance

Read [`PR-GUIDE.md`](../assets/PR-GUIDE.md) and offer to structure the PR description using the reviewer priority tiers and human action checklist.

### Step 5: Confirm completion

Ask the user: "Is the onboarding complete and working as expected? Do you need any adjustments?"

### End of skill

This is the final phase. No further hand-off.