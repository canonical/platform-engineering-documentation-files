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

### Step 4a: Verify `.readthedocs.yaml` build settings

The template generates `.readthedocs.yaml` with default build settings
(`ubuntu-22.04` / Python 3.11). Some downstream repos may use a newer OS
or Python version. Compare the generated file against the backup:

```bash
echo "Generated:" && grep -A2 'build:' .readthedocs.yaml | head -3
echo "Original:" && grep -A2 'build:' /tmp/docs-backup/.readthedocs.yaml | head -3
```

If the downstream used a newer version (e.g., `ubuntu-24.04` / Python 3.13
instead of the template's `ubuntu-22.04` / Python 3.11), ask the user:

> "The generated `.readthedocs.yaml` uses {template values}. The original
> used {downstream values}. Restore the downstream's version?"

If the user confirms, override the `build:` section of the generated
`.readthedocs.yaml` with the values from the backup.

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

### Step 5a: Disable Renovate updates for `docs/**` via `packageRules` (if Renovate is used)

If the downstream repo uses Renovate to manage dependency updates, add a
`packageRules` entry that disables updates for the `docs/` folder so Renovate
does not open PRs against Copier-managed documentation tooling files.

**Use `packageRules`, not `ignorePaths`.** A disabled `packageRules` entry keeps
the docs files visible to Renovate but suppresses update PRs, which is more
explicit and composes cleanly with the other rules most repos already express as
`packageRules`. `ignorePaths` instead stops Renovate from extracting those files
at all, which is a broader, less discoverable behaviour. The target entry is:

```json
{
  "enabled": false,
  "matchFileNames": ["docs/**"]
}
```

Check if `renovate.json` exists:

```bash
ls renovate.json 2>/dev/null && echo "Found renovate.json" || echo "No renovate.json"
```

If `renovate.json` exists, check whether a rule already disables updates for
`docs/**`:

```bash
python3 -c "
import json
data = json.load(open('renovate.json'))
rules = data.get('packageRules', [])
present = any(
    r.get('enabled') is False and 'docs/**' in r.get('matchFileNames', [])
    for r in rules
)
print('PRESENT' if present else 'MISSING')
"
```

Then handle each case:

#### Case 1: no matching rule exists
Prepend the disable rule to `packageRules` (creating the array if absent):

```bash
python3 -c "
import json
with open('renovate.json') as f:
    data = json.load(f)
rule = {'enabled': False, 'matchFileNames': ['docs/**']}
data.setdefault('packageRules', []).insert(0, rule)
with open('renovate.json', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
"
```

#### Case 2: a matching rule already exists
No action needed. Report: "`docs/**` already disabled in Renovate packageRules. Skipping."

> **Note:** If the repo already had `docs/**` in `ignorePaths` from a previous
> onboarding, remove it when adding the `packageRules` entry so the two
> mechanisms don't overlap.

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