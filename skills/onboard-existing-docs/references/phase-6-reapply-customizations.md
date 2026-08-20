---
name: phase-6-reapply-customizations
description: "Phase 6 of the onboard-existing-docs skill. Re-applies downstream customizations by diffing generated files against backups."
---

# Phase 6: Re-Apply Downstream Customizations

**Prerequisites:** Phase 5 (`phase-5-run-copier`) must be complete. Copier must have generated all files successfully.

---

## Instructions

### Step 1: Diff generated files against backups

Run diffs for each file that had downstream customizations:

```bash
diff /tmp/docs-backup/conf.py docs/conf.py
diff /tmp/docs-backup/Makefile docs/Makefile
diff /tmp/docs-backup/requirements.txt docs/requirements.txt
diff /tmp/docs-backup/.gitignore docs/.gitignore
```

### Step 2: Re-apply `conf.py` customizations

Using the `template_uncovered_values` from Phase 2, re-add any:
- Custom Sphinx extensions to the `extensions` list
- Extra `html_context` entries
- Custom `html_theme_options`
- Any other bespoke configuration that was in the original

**Important**: Do not overwrite Copier-managed values. Only add entries that are NOT covered by the template's Copier variables.

### Step 3: Re-apply `Makefile` customizations

Using `downstream_customizations.makefile_targets` from Phase 3, re-add any custom Makefile targets. Append them after the existing targets, preserving the template's standard targets.

### Step 4: Re-apply `requirements.txt` customizations

Using `downstream_customizations.extra_dependencies` from Phase 3, add any extra Python dependencies. Append them at the end of the file with a comment:

```
# Downstream-specific dependencies
my-extra-package==1.2.3
```

### Step 5: Merge `.gitignore` customizations

Using `downstream_customizations.gitignore_patterns` from Phase 3, merge any custom ignore patterns. Append them at the end of the file with a comment:

```
# Downstream-specific ignores
my-custom-pattern/
```

### Step 6: Verify no content files were affected

Confirm that documentation content files from `content_files` (Phase 1) are still present and unchanged:

```bash
ls docs/*.md docs/*.rst docs/_static/ 2>/dev/null
```

### Hand-off to Phase 7

Carry forward:
- `backup_path` — from Phase 4
- `extracted_values` — from Phase 2
- `content_files` — from Phase 1