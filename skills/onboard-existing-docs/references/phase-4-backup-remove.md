---
name: phase-4-backup-remove
description: "Phase 4 of the onboard-existing-docs skill. Backs up existing tooling files and removes only those that overlap with the template."
---

# Phase 4: Back Up and Remove Overlapping Files

**Prerequisites:** Phase 3 (`phase-3-identify-customizations`) must be complete. All values must be confirmed by the user.

---

## Instructions

### Step 1: Create the backup

Run the following from the downstream repo root:

```bash
mkdir /tmp/docs-backup
cp -r docs/ /tmp/docs-backup/
cp .readthedocs.yaml /tmp/docs-backup/ 2>/dev/null || true
```

Verify the backup was created:

```bash
ls /tmp/docs-backup/docs/
```

### Step 1a: Pre-place `_skip_if_exists` files from legacy `.sphinx/` paths (if applicable)

If Phase 1 detected a legacy `docs/.sphinx/` directory (which Step 2 will remove),
check whether it contains files that the template's `_skip_if_exists` would protect
at their new paths. Pre-copy them so Copier preserves them instead of generating
defaults:

```bash
# Pre-place overwrite_links.js to the new template path
test -f docs/.sphinx/_static/js/overwrite_links.js && \
  cp docs/.sphinx/_static/js/overwrite_links.js docs/_static/js/overwrite_links.js

# Pre-place header.html to the new template path
test -f docs/.sphinx/_templates/header.html && \
  cp docs/.sphinx/_templates/header.html docs/_templates/header.html
```

If the target directories (`docs/_static/js/`, `docs/_templates/`) don't exist yet,
create them first:

```bash
mkdir -p docs/_static/js docs/_templates
```

If pre-placement isn't possible (e.g., the target path doesn't exist and can't be
created), skip this step. Fall back to restoring these files from the backup in
Phase 6.

> **Layout note:** Not every legacy repo keeps these files under `.sphinx/`. Many
> already have `overwrite_links.js` at `docs/_static/js/` and `header.html` at
> `docs/_templates/` (the new paths). When that's the case, the `test -f
> docs/.sphinx/...` checks above simply no-op and Copier's `_skip_if_exists`
> preserves the in-place files automatically — nothing to pre-place. Only the
> `.sphinx/`-nested variant needs this step.

### Step 2: Remove only the tooling files that overlap with the template

**CRITICAL: Do NOT remove documentation content files** (`.md`, `.rst`, `_static/`, images, custom CSS, etc.).

Using the `overlapping_files` list from Phase 1, remove only those files:

```bash
rm -rf docs/conf.py docs/Makefile docs/requirements.txt \
       docs/.gitignore docs/_dev docs/.sphinx docs/_templates \
       .readthedocs.yaml
```

**Do not remove `docs/release-notes/template/` when `release_notes_overrides`
(from Phase 1) is non-empty.** Leaving it in place lets Copier's generated files
land alongside the downstream ones so Phase 6 can restore the customized versions
and delete the format-mismatched generated file (e.g. a `.rst.j2` generated next
to a preserved `.md.j2`). Only include `docs/release-notes/template` in the `rm`
above when the downstream templates are unmodified and match the template format.

### Step 2a: Remove stale build artifacts

If `docs/_build/` exists, remove it to prevent stale build output from
confusing the post-onboarding build:

```bash
rm -rf docs/_build
```

### Step 3: Verify content files are still present

Confirm that documentation content files were not accidentally removed:

```bash
ls docs/*.md docs/*.rst docs/_static/ 2>/dev/null
```

If any content files are missing, restore them from the backup immediately:

```bash
cp -r /tmp/docs-backup/docs/<missing-file> docs/
```

### Step 4: Confirm readiness

Tell the user: "Backup created at `/tmp/docs-backup/`. Tooling files removed. Content files preserved. Ready to run Copier."

### Hand-off to Phase 5

Carry forward:
- `backup_path` — `/tmp/docs-backup/`
- `extracted_values` — from Phase 2
- `template_uncovered_values` — from Phase 2
- `downstream_customizations` — from Phase 3
- `content_files` — from Phase 1
- `release_notes_overrides` — from Phase 1