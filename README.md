# Platform Engineering Documentation Files

Cookiecutter template for centrally managing common files in Platform Engineering documentation sets. Downstream repositories use [cruft](https://cruft.github.io/cruft/) to stay in sync with this template.

## Quick start

### Create a new documentation repository

```bash
pip install cruft
cruft create https://github.com/canonical/platform-engineering-documentation-files
```

Answer the prompts (project name, author, GitHub URL, etc.) and cruft will scaffold a new documentation project with all standard files.

### Link an existing repository

If your repository already uses these documentation files:

```bash
cd your-existing-repo
pip install cruft
cruft link https://github.com/canonical/platform-engineering-documentation-files
```

Specify the commit hash that matches your current version of the files (or accept the latest).

### Update from the template

When this template is updated, pull the changes into your downstream repository:

```bash
cruft update
```

Review and accept or reject the proposed changes. To check if updates are available without applying them:

```bash
cruft check
```

### Automated updates via GitHub Actions

Enable the included `.github/workflows/cruft-update.yml` workflow in your repository. Uncomment the `schedule` trigger to receive weekly PRs when the template changes.

## Template variables

| Variable | Default | Description |
|----------|---------|-------------|
| `project_name` | `Project` | Official project/product name |
| `author` | `Canonical Ltd.` | Author for copyright statement |
| `product_page` | *(empty)* | Product website URL (without `https://`) |
| `discourse` | *(empty)* | Discourse instance URL |
| `mattermost` | *(empty)* | Mattermost channel URL |
| `matrix` | *(empty)* | Matrix channel URL |
| `github_url` | *(empty)* | Documentation GitHub repository URL |
| `repo_default_branch` | `main` | Default branch name |
| `repo_folder` | `/docs/` | Docs location in the repository |
| `display_contributors` | `False` | Show contributors on pages |
| `license_name` | *(empty)* | SPDX license identifier |
| `license_url` | *(empty)* | URL to license statement |
| `ogp_site_name` | *project_name* | OpenGraph preview site name |
| `ogp_image` | *(Ubuntu docs illustration)* | OpenGraph preview image URL |
| `html_favicon` | *(empty)* | Path to favicon (omitted if empty) |
| `product_tag` | *(empty)* | Logo tag image path (omitted if empty) |
| `sequential_nav` | *(empty)* | Previous/Next nav: `none`, `prev`, `next`, `both` |
| `source_edit_link` | *(empty)* | GitHub/Launchpad edit link (omitted if empty) |
| `slug` | *(empty)* | RTD slug for documentation.ubuntu.com |
| `llms_txt_description` | *(empty)* | Custom description for llms.txt |
| `manpages_url` | *(empty)* | Manpage URL template (omitted if empty) |
| `disable_feedback_button` | `False` | Disable the feedback button |

## What's included

### Files copied verbatim (identical across all repos)

- `docs/_dev/` — Dev tooling: Vale config fetcher, update script, pa11y, pymarkdownlnt, pre-commit hooks
- `docs/_templates/` — Sphinx HTML header/footer templates
- `docs/Makefile` — Build orchestration (install, html, spelling, vale, etc.)
- `docs/requirements.txt` — Pinned Python dependencies
- `docs/release-notes/template/` — Release notes YAML schemas and Jinja2 template
- `.readthedocs.yaml` — Read the Docs build configuration

### Files templatized (customized per repo)

- `docs/conf.py` — Sphinx configuration with project-specific values filled from template variables

## Skipping files during updates

If downstream repos have customized certain files and want to prevent cruft from overwriting them, add those paths to the `skip` list in `.cruft.json`:

```json
{
    "skip": [
        "docs/_templates/header.html_"
    ]
}
```

Glob patterns are supported.