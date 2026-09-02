# Opinions in this solution

This page explains the design decisions and trade-offs behind the
Platform Engineering documentation files solution.

## Why Copier?

We chose [Copier](https://copier.readthedocs.io/) over alternatives like
Cookiecutter or manual copy-paste for several reasons:

- **Bidirectional updates.** Copier's `copier update` command lets downstream
  repos pull in template changes while preserving their project-specific values.
  This is the foundation of the central-management model.
- **Declarative questionnaire.** The `copier.yml` file defines all project-specific
  variables in one place, with types, defaults, and help text. This makes the
  template self-documenting.
- **Jinja2 templating.** Copier uses Jinja2, the same templating engine as Sphinx,
  so the template syntax is familiar to documentation maintainers.
- **`.copier-answers.yml` as source of truth.** Copier records every answer in a
  machine-readable file, making updates reproducible and auditable.

## Why Sphinx + the Canonical Sphinx stack?

- **Sphinx** is the standard documentation tool across Canonical. Using it ensures
  consistency with other projects and access to the Canonical Sphinx theme.
- **The Canonical Sphinx stack** (`canonical/sphinx-stack`) provides a curated set
  of Sphinx extensions, a branded theme, and developer tooling (vale, pa11y,
  pre-commit). This template wraps that stack so downstream repos get it without
  manual configuration.

## What's included — and why

| Area | Rationale |
|---|---|
| `docs/conf.py` (templated) | Every project needs Sphinx config. Templating it lets us fill in project-specific values from the Copier questionnaire. |
| `docs/Makefile`, `docs/requirements.txt` (static) | Standard build tooling that doesn't vary between projects. |
| `docs/_dev/` (static) | Developer tooling (vale, pa11y, pre-commit, pymarkdown, sphinx-stack updater) that every PE docs project should use. |
| `docs/_templates/` (static) | HTML header and footer templates for the Canonical theme. |
| `.readthedocs.yaml` (static) | Standard RTD build configuration. |
| `docs/release-notes/template/` (static) | Release note artifact templates for consistent changelog formatting. |

## What's deliberately excluded

- **Documentation content** (`.md`, `.rst`, images, `_static/` assets). These are
  project-specific and not managed by the template.
- **CI/CD beyond the callable workflow.** Each downstream repo manages its own CI.
  The template provides a reusable GitHub Actions workflow for automated Copier
  updates, but doesn't impose a CI structure.

## Template vs. static files

Files in the template fall into two categories:

- **Templated files** (`.jinja` suffix) are rendered with project-specific values
  from `.copier-answers.yml` at generation time. Example: `conf.py.jinja` → `docs/conf.py`.
- **Static files** are copied as-is. They contain no project-specific values and
  are identical across all downstream repos. Example: `docs/Makefile`.

This distinction keeps the template maintainable: only files that genuinely vary
between projects are templated.

## Single source of truth

This repository is the single source of truth for documentation tooling across
Platform Engineering. When a bug is fixed or an improvement is made here,
downstream repos pull it in through `copier update`. This eliminates the drift that
occurs when each repo maintains its own copy of the same tooling files.
