---
name: phase-7-validate-commit
description: "Phase 7 of the onboard-existing-docs skill. Validates the build and commits the changes."
---

# Phase 7: Validate and Commit

**Prerequisites:** Phase 6 (`phase-6-reapply-customizations`) must be complete. All customizations must be re-applied.

---

## Instructions

### Step 1: Test the build

Run the Sphinx build from the `docs/` directory:

```bash
cd docs && make html
```

### Step 2: Diagnose build failures

If the build fails, diagnose and fix before committing. Common issues:

| Symptom | Likely cause | Fix |
|---|---|---|
| `Extension error` | Missing custom Sphinx extension | Add the extension to `docs/requirements.txt` and re-run `make html` |
| `WARNING: unknown configuration value` | Custom `html_theme_options` not recognized | Verify the option name against the theme documentation |
| Broken references / `WARNING: undefined label` | Changed `html_context` values affecting link generation | Check `github_url`, `repo_default_branch`, `repo_folder` values |
| Missing `_static/` assets | Assets referenced in old config but not present | Copy missing assets from the backup: `cp /tmp/docs-backup/docs/_static/<file> docs/_static/` |
| `document isn't included in any toctree` | Content files not in a toctree | This is expected for content files — ensure they're included in an existing `index.md` toctree |

### Step 3: Fix and retry

After each fix, re-run `make html`. Continue until the build succeeds with no errors.

### Step 4: Run additional checks (optional but recommended)

```bash
make spelling    # Check spelling
make linkcheck   # Check external links
make vale        # Check style guide compliance
make lint-md     # Check Markdown formatting
```

### Step 5: Update `.licenserc.yaml` (if present)

If the downstream repo has a `.licenserc.yaml` file that checks license headers,
add `.copier-answers.yml` to its `paths-ignore` list. The file is auto-generated
by Copier and should not be checked for license headers.

Check if `.licenserc.yaml` exists:

```bash
ls .licenserc.yaml 2>/dev/null && echo "Found .licenserc.yaml" || echo "No .licenserc.yaml"
```

If it exists, add `.copier-answers.yml` to the `paths-ignore` list. The entry
should be placed alongside other generated/config files that are already ignored.

### Step 5a: Add `docs/**` to Renovate `ignorePaths` (if Renovate is used)

If the downstream repo uses Renovate to manage dependency updates, the `docs/`
folder must be added to `"ignorePaths"` in `renovate.json` so Renovate does not
open PRs against Copier-managed documentation tooling files.

Check if `renovate.json` exists:

```bash
ls renovate.json 2>/dev/null && echo "Found renovate.json" || echo "No renovate.json"
```

If `renovate.json` exists, handle each case:

#### Case 1: `ignorePaths` does not exist
Add it with `docs/**`:

```bash
python3 -c "
import json
with open('renovate.json') as f:
    data = json.load(f)
data['ignorePaths'] = ['docs/**']
with open('renovate.json', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
"
```

#### Case 2: `ignorePaths` exists but does not contain `docs/**`
Append `docs/**` to the existing array:

```bash
python3 -c "
import json
with open('renovate.json') as f:
    data = json.load(f)
if 'docs/**' not in data.get('ignorePaths', []):
    data['ignorePaths'].append('docs/**')
with open('renovate.json', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
"
```

#### Case 3: `docs/**` is already in `ignorePaths`
No action needed. Report: "`docs/**` already in Renovate ignorePaths. Skipping."

### Step 6: Commit

Once the build succeeds, instruct the user to commit:

```bash
git add .
git commit -m "Onboard documentation tooling to Copier-based management"
```

### Hand-off to Phase 8

Carry forward:
- `backup_path` — from Phase 4
- `extracted_values` — from Phase 2