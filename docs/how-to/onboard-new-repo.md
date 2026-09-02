# How to onboard a repository with no documentation files

If your repository does not yet have any documentation tooling files (no
Sphinx config, Makefile, or Read the Docs configuration), follow this
process to set up the documentation scaffold from scratch.

## Prerequisites

- Python 3.10+
- Git 2.27+
- Copier installed: `pipx install copier` or `uv tool install copier`

## Generate the documentation scaffold

From the root of your downstream repository, run:

```bash
copier copy gh:canonical/platform-engineering-documentation-files.git .
```

Copier will prompt you with a series of questions about your project (name,
URLs, license, and so on). Answer them to generate your documentation
scaffold. See the [Copier variables reference](../reference/copier-answers-yml.md)
for details on each question.

## What gets generated

| File | Purpose |
|---|---|
| `docs/conf.py` | Sphinx configuration with your project's values filled in |
| `docs/Makefile` | Build tooling for local development |
| `docs/requirements.txt` | Python dependencies for building the docs |
| `docs/.gitignore` | Ignore rules for build artifacts |
| `docs/_dev/` | Developer tooling (vale, pa11y, pre-commit, and more) |
| `docs/_templates/` | HTML header and footer templates |
| `docs/release-notes/template/` | Release note artifact templates |
| `.readthedocs.yaml` | Read the Docs build configuration |
| `.copier-answers.yml` | Records your answers for future updates |

## Validate and commit

Test that the generated documentation builds correctly:

```bash
cd docs && make html
```

If the build succeeds, commit the generated files:

```bash
git add .
git commit -m "Initialize documentation scaffold from platform-engineering-documentation-files"
```

## After onboarding

- Your `.copier-answers.yml` is now the source of truth for project-specific
  values. Do not edit it manually.
- To pull in future template updates, run `copier update` from the repo root.
  See [How to update a downstream repository](update-downstream-repo.md).
- If you need to change a project value (for example, a new Discourse URL),
  update `.copier-answers.yml` and re-run `copier update`.
- If you are using Read the Docs, create a project there and configure it to
  build from your repository.



