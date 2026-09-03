# Platform Engineering Documentation Files

Central management and maintenance solution for common files in Platform Engineering documentation sets.

This repository is a [Copier](https://copier.readthedocs.io/) template that provides a
standardised Sphinx documentation scaffold for downstream Platform Engineering
repositories. Downstream repos use Copier to generate and later update their
documentation tooling from this single source of truth.

Documentation is available in the [`docs/`](docs/index.md) directory,
organized around the [Diátaxis](https://diataxis.fr/) framework.

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

### Get started

From the root of your downstream repository:

```bash
copier copy gh:canonical/platform-engineering-documentation-files.git .
```

Copier will prompt you with a series of questions about your project (name, URLs,
license, etc.). Answer them to generate your documentation scaffold.

After generation, review the changes and commit.

## Contributing to this template

To make changes to the template itself:

1. Edit files under `template/` — these are what get rendered into downstream repos.
   - Files ending in `.jinja` are Jinja2 templates that use variables from `copier.yml`.
   - Files without `.jinja` are copied as-is.
2. If you add new variables, update `copier.yml` with the corresponding questions.
3. Test your changes.
4. Submit a pull request.

## Testing

The repository includes an integration test that validates the template generates a
working Sphinx documentation project. It runs `copier copy` with two answer scenarios
and builds the output with `make html`, which is configured to fail on any warning.
The tests run locally and are required to pass on all pull requests.

* Full scenario (all fields populated): `bash tests/test_build.sh`
* Minimal scenario (only required fields): `bash tests/test_build.sh minimal`

**Requirements**: Python 3.10+ with the `venv` module, Git 2.27+, GNU Make, and Copier (`pipx install copier`).
