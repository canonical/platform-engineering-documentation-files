---
name: phase-5-run-copier
description: "Phase 5 of the onboard-existing-docs skill. Runs Copier with the confirmed values to generate the documentation scaffold."
---

# Phase 5: Run Copier

**Prerequisites:** Phase 4 (`phase-4-backup-remove`) must be complete. Overlapping files must be removed and backed up.

---

## Instructions

### Step 1: Determine execution mode

Check whether the user wants interactive or non-interactive Copier execution.

- **Interactive**: Copier prompts for each value. Use this when the user wants to review each value as it's entered.
- **Non-interactive**: Pass all values via `--data` flags. Use this when all values have been confirmed and the user wants a single command.

Ask the user which mode they prefer (see [`question-bank.md`](question-bank.md), Section "Copier Execution Mode").

### Step 2: Run Copier interactively

From the downstream repo root:

```bash
copier copy gh:canonical/platform-engineering-documentation-files.git .
```

Answer each prompt with the values from `extracted_values` (confirmed in Phase 2).

### Step 3: Run Copier non-interactively (alternative)

Construct the command using `--data` flags for each confirmed value. Use `--defaults` to skip prompts for unspecified values and `--overwrite` to allow Copier to write into the existing `docs/` directory (which still contains content files):

```bash
copier copy --defaults --overwrite \
  --data "project=MyProject" \
  --data "author=Canonical Ltd." \
  --data "product_page=charmhub.io/my-charm" \
  --data "discourse=https://discourse.charmhub.io" \
  --data "matrix=https://matrix.to/#/#my-channel:ubuntu.com" \
  --data "github_url=https://github.com/canonical/my-repo" \
  --data "source_edit_link=https://github.com/canonical/my-repo" \
  --data "docs_host=canonical.com" \
  --data "rtd_slug=juju/docs/my-charm" \
  --data "old_domain=canonical-my-charm.readthedocs-hosted.com" \
  --data "new_domain=canonical.com/juju/docs/my-charm" \
  --data "display_contributors=False" \
  gh:canonical/platform-engineering-documentation-files.git .
```

The example above shows the full set typically needed for a legacy Juju charm
repo. Include a `--data` flag for every value that differs from the template
default (in practice this almost always includes `source_edit_link`, `rtd_slug`,
`docs_host`, `old_domain`, and `new_domain`, which the shorter examples omit).

Only include `--data` flags for non-default values. Omit flags for variables where the default is acceptable.

### Step 4: Verify generation

After Copier completes, verify that the expected files were generated:

```bash
ls docs/conf.py docs/Makefile docs/requirements.txt docs/.gitignore
ls docs/_dev/
ls docs/_templates/
ls docs/release-notes/template/
ls .readthedocs.yaml .copier-answers.yml
```

### Step 4a: Verify `_skip_if_exists` files were preserved

Copier's `_skip_if_exists` mechanism protects three files from being overwritten:
`docs/_static/js/overwrite_links.js`, `docs/_templates/header.html`, and
`docs/redirects.txt`. Verify they're intact after Copier runs:

```bash
git diff --stat docs/_static/js/overwrite_links.js docs/_templates/header.html docs/redirects.txt 2>/dev/null
```

If any of these files show as "modified" or "deleted" in the diff, the
`_skip_if_exists` mechanism didn't apply correctly. Restore them from the backup
immediately:

```bash
cp /tmp/docs-backup/docs/<path-to-file> docs/<path-to-file>
```

### Step 5: Verify `.copier-answers.yml`

Read `.copier-answers.yml` and confirm it contains the correct values matching `extracted_values`. If any value is wrong, do not edit `.copier-answers.yml` manually — re-run `copier copy` with corrected `--data` flags.

### Hand-off to Phase 6

Carry forward:
- `backup_path` — from Phase 4
- `extracted_values` — from Phase 2
- `template_uncovered_values` — from Phase 2
- `downstream_customizations` — from Phase 3
- `content_files` — from Phase 1
- `release_notes_overrides` — from Phase 1