# Platform Engineering Documentation Files

Central management and maintenance solution for common files in Platform Engineering documentation sets.

This repository is a [Copier](https://copier.readthedocs.io/) template that provides a
standardised Sphinx documentation scaffold for downstream Platform Engineering
repositories. Downstream repos use Copier to generate and later update their
documentation tooling from this single source of truth.

## What's included

| Area | Files | Type |
|------|-------|------|
| Sphinx configuration | `docs/conf.py` | Templated per project |
| Build tooling | `docs/Makefile`, `docs/requirements.txt` | Static |
| Developer tooling | `docs/_dev/` (vale, pa11y, pre-commit, pymarkdown, sphinx-stack updater) | Static |
| HTML templates | `docs/_templates/` (header, footer) | Static |
| Read the Docs config | `.readthedocs.yaml` | Static |
| Release note templates | `docs/release-notes/template/` | Static |

## Onboarding a downstream repository

### Prerequisites

- Python 3.10+
- Git 2.27+
- Copier installed: `pipx install copier` or `uv tool install copier`

### First-time setup

From the root of your downstream repository:

```bash
copier copy gh:canonical/platform-engineering-documentation-files.git .
```

Copier will prompt you with a series of questions about your project (name, URLs,
license, etc.). Answer them to generate your documentation scaffold.

After generation, review the changes and commit:

```bash
git add .
git commit -m "Initialize documentation scaffold from platform-engineering-documentation-files"
```

### What gets generated

- **`docs/conf.py`** — Sphinx configuration with your project's values filled in
- **`docs/Makefile`**, **`docs/requirements.txt`**, **`docs/.gitignore`** — Build tooling
- **`docs/_dev/`** — Developer tooling (vale, pa11y, pre-commit, etc.)
- **`docs/_templates/`** — HTML header and footer templates
- **`docs/release-notes/template/`** — Release note artifact templates
- **`.readthedocs.yaml`** — Read the Docs build configuration
- **`.copier-answers.yml`** — Records your answers for future updates (do not edit manually)

### Post-setup steps

1. **Set up Read the Docs** — If you're using Read the Docs, configure your project
   there to build from your repository.
2. **Customise further** — Edit `docs/conf.py` for any additional Sphinx configuration
   not covered by the Copier questionnaire.

## Onboarding a repository that already has documentation tooling

If your repository already contains unmanaged copies of the documentation
tooling files (Sphinx config, Makefile, requirements, etc.), follow this
process to bring them under Copier management.

> **AI-assisted onboarding**: An AI agent skill is available to guide you
> through this process automatically. See
> [`skills/onboard-existing-docs/SKILL.md`](skills/onboard-existing-docs/SKILL.md)
> for the full agent workflow.

### Preparation

1. **Audit your existing files** against the [list of generated files](#what-gets-generated).
   Any file that exists in both your repo and the template will be overwritten.

2. **Extract project-specific values** from your existing `docs/conf.py`.
   Map each value to the corresponding Copier question (see `copier.yml` for
   the full list). Pay special attention to:
   - `project`, `author`, `copyright`
   - All entries in `html_context` (product page, Discourse, Mattermost,
     Matrix, GitHub URL, branch, folder, product tag, contributors)
   - `ogp_image`, `html_favicon`
   - Any custom Sphinx extensions or configuration not covered by the template

3. **Identify downstream-only customizations** — things in your current
   `conf.py`, `Makefile`, or `requirements.txt` that are unique to your
   project and not part of the standard template. You'll re-apply these
   after generation.

### Onboarding steps

1. **Back up** your existing tooling files:

   ```bash
   mkdir /tmp/docs-backup
   cp -r docs/ /tmp/docs-backup/
   cp .readthedocs.yaml /tmp/docs-backup/ 2>/dev/null || true
   ```

2. **Remove only the tooling files** that overlap with the template.
   Do **not** remove your documentation content (`.md`, `.rst`, `_static/`,
   images, etc.):

   ```bash
   rm -rf docs/conf.py docs/Makefile docs/requirements.txt \
          docs/.gitignore docs/_dev docs/_templates \
          docs/release-notes/template .readthedocs.yaml
   ```

3. **Run Copier** with your extracted values:

   ```bash
   copier copy gh:canonical/platform-engineering-documentation-files.git .
   ```

4. **Re-apply downstream customizations** by comparing the newly generated
   files against your backup:

   ```bash
   diff /tmp/docs-backup/conf.py docs/conf.py
   diff /tmp/docs-backup/Makefile docs/Makefile
   diff /tmp/docs-backup/requirements.txt docs/requirements.txt
   ```

   Add back any project-specific extensions, Makefile targets, or extra
   Python dependencies.

5. **Test the build** and commit:

   ```bash
   cd docs && make html
   git add .
   git commit -m "Onboard documentation tooling to Copier-based management"
   ```

### After onboarding

- Your `.copier-answers.yml` is now the source of truth for project-specific
  values. Do not edit it manually.
- To pull in future template updates, run `copier update` from the repo root.
- If you need to change a project value (e.g., a new Discourse URL), update
  `.copier-answers.yml` and re-run `copier update`.

## Updating an existing downstream repository

When this template repository is updated (new tooling, bug fixes, new Sphinx extensions),
downstream repos can pull in the changes:

```bash
copier update
```

Copier will merge template changes into your repository, preserving your project-specific
values from `.copier-answers.yml`. Review the diff, resolve any conflicts, and commit.

### What Copier updates

- All static files (Makefile, requirements, `_dev/`, `_templates/`, workflows, etc.)
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

### What it does

1. Checks out your repository.
2. Runs `copier update --defaults --conflict inline` to pull in template changes non-interactively.
3. Opens a pull request with the changes using `canonical/create-pull-request`.

### Conflict handling

Conflicts are rendered as inline Git merge markers (`<<<<<<<` / `>>>>>>>`) in the
pull request diff. Review the PR and resolve conflicts manually before merging.

If a previous update PR was closed without merging, the next run force-updates the
same branch. If the template hasn't changed since the last update, no PR is created.

### Schedule

The schedule is controlled by the downstream repository (the `cron` value in the
workflow file). Each downstream repo can choose its own cadence.

## Contributing to this template

To make changes to the template itself:

1. Edit files under `template/` — these are what get rendered into downstream repos.
   - Files ending in `.jinja` are Jinja2 templates that use variables from `copier.yml`.
   - Files without `.jinja` are copied as-is.
2. If you add new variables, update `copier.yml` with the corresponding questions.
3. Test your changes using the integration test:
   ```bash
   # Run both scenarios
   bash tests/test_build.sh full && bash tests/test_build.sh minimal
   ```
4. Submit a pull request.

### Template structure

```
├── copier.yml                          # Questions and Copier settings
├── {{ _copier_conf.answers_file }}.jinja  # Answers file template
├── README.md                           # This file
├── skills/                             # AI agent skills for onboarding workflows
│   └── onboard-existing-docs/          # Skill for onboarding pre-existing doc repos
└── template/                           # _subdirectory: template
    ├── .readthedocs.yaml
    ├── docs/
    │   ├── conf.py.jinja               # Templated Sphinx config
    │   ├── Makefile
    │   ├── requirements.txt
    │   ├── .gitignore
    │   ├── _dev/                       # Developer tooling
    │   ├── _templates/                 # HTML templates
    │   └── release-notes/template/     # Release note artifacts
    └── {{ _copier_conf.answers_file }}.jinja
```

## Testing

The repository includes an integration test that validates the template generates a
working Sphinx documentation project. It runs `copier copy` with two answer scenarios
and builds the output with `make html`, which is configured to fail on any warning.

### Running locally

```bash
# Full scenario (all fields populated) — default
bash tests/test_build.sh

# Or explicitly:
bash tests/test_build.sh full

# Minimal scenario (only required fields)
bash tests/test_build.sh minimal
```

**Requirements**: Python 3.10+ with the `venv` module, Git 2.27+, GNU Make, and Copier (`pipx install copier`).

### CI

A GitHub Actions workflow (`.github/workflows/test.yml`) runs both scenarios on every
push and pull request to `main`.