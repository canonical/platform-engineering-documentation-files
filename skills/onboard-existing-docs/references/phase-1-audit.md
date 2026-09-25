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

Inventory the documentation directory. Legacy repos often contain a build
virtualenv (`docs/.sphinx/venv/`) and build output (`docs/_build/`) with tens of
thousands of files, so a plain `find docs/ -type f` is unusable. Prefer listing
only git-tracked files:

```bash
git ls-files docs/ | grep -v '^docs/_build/' | sort
```

If you also need to see untracked files (e.g. newly added content not yet
committed), exclude the noisy directories explicitly:

```bash
find docs/ -type f \
  -not -path '*/venv/*' \
  -not -path '*/.venv/*' \
  -not -path 'docs/_build/*' \
  -not -path '*/node_modules/*' | sort
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

#### Release-notes templates: check for downstream customization

`docs/release-notes/template/*` is listed as an overlap above, but many repos
**customize** these templates or use a different format than the template ships.
The template provides `release-template.rst.j2` (reStructuredText); markdown-based
projects instead keep a `release-template.md.j2`. The artifact YAML templates
(`_change-artifact-template.yaml`, `_release-artifact-template.yaml`) may also
diverge.

Detect this before treating the directory as a plain overlap:

```bash
ls docs/release-notes/template/ 2>/dev/null
```

- If a `release-template.md.j2` exists (and the docs are markdown), the project
  uses a **markdown release-notes workflow**. Copier will generate the template's
  `release-template.rst.j2` alongside it — the generated `.rst.j2` must be
  **removed** in Phase 6, and the downstream `.md.j2` preserved.
- Compare each artifact YAML template against the template version. If they
  differ, the downstream versions are customizations to restore in Phase 6:

  ```bash
  for f in _change-artifact-template.yaml _release-artifact-template.yaml; do
    diff docs/release-notes/template/$f \
         <template-repo>/template/docs/release-notes/template/$f \
      >/dev/null 2>&1 && echo "$f: identical" || echo "$f: DIFFERS (preserve downstream)"
  done
  ```

Record any customized or format-mismatched files in `release_notes_overrides`.
Do **not** remove `docs/release-notes/template/` wholesale in Phase 4 — leave it
in place so Phase 6 can restore the downstream versions and drop the mismatched
generated file.

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
- `release_notes_overrides` — customized or format-mismatched release-notes
  template files to preserve/restore (empty if none)