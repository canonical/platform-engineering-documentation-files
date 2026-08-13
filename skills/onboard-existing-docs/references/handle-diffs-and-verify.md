---
name: handle-diffs-and-verify
description: "Phase 3 of the onboard-existing-docs skill. Handles verbatim file diffs (accept template, keep downstream, or manual merge), flags extra files, verifies the documentation build, and documents the skip list."
---

# handle-diffs-and-verify

**Prerequisites:** This is Phase 3 of the `onboard-existing-docs` skill.
Phases 1 and 2 must be completed first. You need:
- `repo_path` — absolute path to the downstream repository
- `triage_report` — the JSON report from the triage script
- The confirmed `docs/conf.py` variable mappings from Phase 2

---

## Instructions

### Step 1: Review verbatim files with diffs

From the triage report, identify all files with status `minor_diff` or
`major_diff`. These are verbatim files that differ between the template and the
downstream repository.

For each such file, present the diff to the user. Use `diff` to show the
differences:

```bash
diff -u <template_root>/{{cookiecutter.project_name}}/<file_path> <repo_path>/<file_path>
```

Or read both files and present a summary of the differences.

For each file, ask the user one of these questions:

> **"The file `<file_path>` differs from the template. What should I do?"**

Options:
1. **Accept the template version** — overwrite the downstream file with the
   template version. The downstream customizations will be lost.
2. **Keep the downstream version** — add the file to the `.cruft.json` skip
   list. The file will no longer receive template updates.
3. **Manual merge** — skip this file for now. The user will manually merge the
   changes later.

Record the user's decision for each file.

### Step 2: Apply accept decisions

For files where the user chose **Accept the template version**, copy the
template file over the downstream file:

```bash
cp <template_root>/{{cookiecutter.project_name}}/<file_path> <repo_path>/<file_path>
```

### Step 3: Apply skip decisions

For files where the user chose **Keep the downstream version**, add them to the
`skip` list in `.cruft.json`.

Read the current `.cruft.json`:

```
Read <repo_path>/.cruft.json
```

Add or update the `skip` field. If it doesn't exist, create it. The `skip`
field is an array of file path glob patterns:

```json
{
  "skip": [
    "docs/_templates/header.html",
    "docs/Makefile"
  ]
}
```

Write the updated `.cruft.json` back to the downstream repository.

**Important:** After adding files to the skip list, remind the user:

> ⚠️ **The following files have been added to the skip list and will no longer
> receive updates from the template:**
> - `<file_path>`
>
> You will need to manually keep these files in sync with template changes.

### Step 4: Handle extra files

From the triage report, review the `extras` list — files in template-managed
directories that are not part of the template.

Present these to the user:

> **"The following files exist in template-managed directories but are not part
> of the template. They will not be affected by cruft:"**
> - `<extra_file_path>`

No action is needed for these files. They are simply noted for the user's
awareness.

### Step 5: Handle missing files

From the triage report, identify files with status `missing`. These are
template files that don't exist in the downstream repository.

If `cruft update` in Phase 2 did not create them, copy them from the template:

```bash
cp <template_root>/{{cookiecutter.project_name}}/<file_path> <repo_path>/<file_path>
```

### Step 6: Verify the documentation build

Run the documentation build to confirm everything works:

```bash
cd <repo_path>/docs
make clean
make install
make html
```

**Check for errors:**
- If `make install` fails: check the pip install log. There may be dependency
  conflicts or network issues.
- If `make html` fails: read the Sphinx build output. Common issues:
  - Missing or incorrect values in `conf.py` (check the variable mappings from
    Phase 2)
  - Missing files that should have been created by cruft
  - Broken intersphinx mappings
  - Missing `_templates/` or `_dev/` files

**If the build fails:**
1. Read the error output carefully.
2. Identify the root cause.
3. Fix the issue if it's within the scope of this skill (e.g., a missing file
   that should have been copied, an incorrect conf.py value).
4. Re-run `make html` until it passes.
5. If the issue cannot be resolved within the scope of this skill, report it to
   the user and stop.

**If the build passes:** Confirm with the user:

> ✅ **The documentation build passes. The onboarding is complete.**

### Step 7: Summarize the onboarding

Provide a final summary to the user:

```
## Onboarding Summary

- **Repository:** <repo_path>
- **Template commit:** <commit_hash>
- **conf.py variables mapped:** 22/22
- **Files accepted from template:** <N>
- **Files kept from downstream (skip list):** <N>
- **Files manually merged:** <N>
- **Extra files noted:** <N>
- **Build verification:** ✅ passed / ❌ failed
```

### Step 8: Remind about ongoing maintenance

Remind the user about ongoing template updates:

> **Next steps for ongoing maintenance:**
>
> - Run `cruft check` to see if template updates are available.
> - Run `cruft update` to apply template updates.
> - Files in the skip list will not be updated automatically — you'll need to
>   manually review template changes for those files.
> - Enable the `.github/workflows/cruft-update.yml` workflow (if available) to
>   receive automated PRs when the template changes.