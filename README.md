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

## Contributing to this template

To make changes to the template itself:

1. Edit files under `template/` — these are what get rendered into downstream repos.
   - Files ending in `.jinja` are Jinja2 templates that use variables from `copier.yml`.
   - Files without `.jinja` are copied as-is.
2. If you add new variables, update `copier.yml` with the corresponding questions.
3. Test your changes by generating a project locally:
   ```bash
   copier copy . /tmp/test-output
   ```
4. Submit a pull request.

### Template structure

```
├── copier.yml                          # Questions and Copier settings
├── {{ _copier_conf.answers_file }}.jinja  # Answers file template
├── README.md                           # This file
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