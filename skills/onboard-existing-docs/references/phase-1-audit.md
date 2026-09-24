---
name: phase-1-audit
description: "Phase 1 of the onboard-existing-docs skill. Audits the downstream repo for files that overlap with the template."
---

# Phase 1: Audit Existing Files

**Prerequisites:** This is Phase 1 of the `onboard-existing-docs` skill. See the parent [SKILL.md](../SKILL.md) for the full workflow overview.

---

## Instructions

### Step 0: Ensure you're on a feature branch

Check the current branch. If you're on `main`, create a new feature branch
before making any changes:

```bash
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" = "main" ]; then
  git checkout -b docs/onboard-copier-management
  echo "Created branch docs/onboard-copier-management"
else
  echo "Already on branch: $CURRENT_BRANCH"
fi
```

All onboarding work should happen on a feature branch. The PR will be opened
from this branch against `main`.

### Step 1: List the downstream `docs/` directory

Run the following to inventory the downstream repo's documentation directory:

```bash
find docs/ -type f | sort
```

Also check for root-level config files:

```bash
ls -la .readthedocs.yaml 2>/dev/null || echo "No .readthedocs.yaml found"
```

### Step 2: Compare against the template's generated file list

The template generates these files in the downstream repo:

| Template source | Downstream output |
|---|---|
| `conf.py.jinja` | `docs/conf.py` |
| `Makefile` | `docs/Makefile` |
| `requirements.txt` | `docs/requirements.txt` |
| `.gitignore` | `docs/.gitignore` |
| `_dev/*` | `docs/_dev/*` |
| `_templates/*` | `docs/_templates/*` |
| `release-notes/template/*` | `docs/release-notes/template/*` |
| `.readthedocs.yaml` | `.readthedocs.yaml` |
| `{{ _copier_conf.answers_file }}.jinja` | `.copier-answers.yml` |

Additionally, older downstream repos may have a **legacy `.sphinx/` directory**
from the pre-template starter pack. The template replaces this with `docs/_dev/`,
so `.sphinx/` is also an overlapping file. Check for it:

```bash
ls -d docs/.sphinx/ 2>/dev/null && echo "Found legacy .sphinx/ directory" || echo "No legacy .sphinx/ directory"
```

If `docs/.sphinx/` exists, add it to `overlapping_files` — it will be removed in Phase 4.

#### Files skipped by `_skip_if_exists`

The template's `copier.yml` defines `_skip_if_exists` for certain files. These
will **not** be overwritten by Copier even if they exist downstream:

| File | Behaviour |
|---|---|
| `docs/redirects.txt` | Skipped if it already exists |
| `docs/_templates/header.html` | Skipped if it already exists |
| `docs/_static/js/overwrite_links.js` | Skipped if it already exists |

Do **not** add these to `overlapping_files`. Flag them in the audit report as
"preserved — skipped by `_skip_if_exists`."

### Step 3: Identify overlapping files

For each file in the template's output list, check if it exists in the downstream repo. Build a list of overlapping files.

### Step 4: Report to the user

Report: "I found N files that overlap with the template. These will be overwritten during onboarding."

List each overlapping file with its path.

### Step 5: Identify documentation content files to preserve

List all files under `docs/` that are **not** in the overlapping list — these are documentation content files (`.md`, `.rst`, `_static/`, images, custom CSS, etc.) that must be preserved.

### Hand-off to Phase 2

Carry forward:
- `overlapping_files` — list of files that will be overwritten
- `content_files` — list of documentation content files to preserve