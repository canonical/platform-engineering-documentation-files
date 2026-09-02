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

## Further reading

Detailed documentation is available in the [`docs/`](docs/index.md) directory,
organised around the [Diátaxis](https://diataxis.fr/) framework:

| Section | What you'll find |
|---|---|
| [Explanation](docs/explanation/index.md) | Why this solution exists and the design decisions behind it |
| [How-to guides](docs/how-to/index.md) | Step-by-step instructions for onboarding existing repos, setting up RTD, and updating downstream repos |
| [Reference](docs/reference/index.md) | Copier variable reference, skill documentation, and the update lifecycle |

### Common tasks

- **[Onboard a repo that already has docs tooling](docs/how-to/onboard-existing-repo.md)** — bring unmanaged Sphinx config, Makefile, and requirements under Copier management
- **[Set up RTD for a new project](docs/how-to/set-up-new-rtd.md)** — understand the generated `.readthedocs.yaml` and verify your build
- **[Update a downstream repo](docs/how-to/update-downstream-repo.md)** — pull in template changes manually or with automated GitHub Actions
- **[Copier variables reference](docs/reference/copier-answers-yml.md)** — every variable, its type, default, and where it's used
- **[Solution update lifecycle](docs/reference/update-lifecycle.md)** — how changes flow from sphinx-stack through this template to downstream repos

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