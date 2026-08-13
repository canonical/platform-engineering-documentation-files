---
name: onboard-existing-docs
description: >
  Onboards a downstream repository that already has unmanaged documentation
  tooling files (Sphinx config, Makefile, requirements, etc.) into the
  Copier-based platform-engineering-documentation-files management solution.
  Preserves downstream customizations while bringing tooling under central
  management.
  WHEN: onboard pre-existing docs repo, migrate unmanaged Sphinx docs to
  Copier template, bring existing documentation tooling under central
  management, convert standalone docs to platform-engineering-docs scaffold.
license: Apache-2.0
metadata:
  author: Canonical/platform-engineering
  summary: Onboard a downstream repo with pre-existing documentation tooling into the Copier-based central management solution
  version: "1.0.0"
  tags:
    - canonical
    - platform-engineering
    - documentation
    - copier
    - sphinx
    - onboarding
---

# Onboard Existing Documentation

Inspect first. Preserve downstream customizations. Generate only after
understanding what exists.

## Skill Order

- Run this skill when a downstream repository already contains unmanaged
  documentation tooling files and needs to be brought under Copier management.
- This skill does not hand off to other skills; it is self-contained.

## Prerequisites Check

Before starting, verify the downstream repository has:

- Python 3.10+
- Git 2.27+
- Copier installed (`pipx install copier` or `uv tool install copier`)

If any prerequisite is missing, tell the user to install it and stop.

## Workflow

### Phase 1: Audit existing files

1. List the downstream repo's `docs/` directory and root-level config files.
2. Compare against the template's generated file list. The template generates
   these files in the downstream repo:

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

3. Identify which of these files already exist in the downstream repo.
4. Report to the user: "I found N files that overlap with the template. These
   will be overwritten during onboarding."

### Phase 2: Extract project-specific values

1. Read the downstream `docs/conf.py` and extract every project-specific value.
   Map each to the corresponding Copier question variable from `copier.yml`:

   | In existing `conf.py` | Copier variable | Notes |
   |---|---|---|
   | `project = "..."` | `project` | |
   | `author = "..."` | `author` | |
   | `copyright = ...` | (not a direct variable) | Template uses `datetime.date.today().year` |
   | `ogp_image = "..."` | `ogp_image` | |
   | `html_favicon = "..."` | `html_favicon` | May be absent |
   | `html_context["product_page"]` | `product_page` | |
   | `html_context["product_tag"]` | `product_tag` | May be absent |
   | `html_context["discourse"]` | `discourse` | |
   | `html_context["mattermost"]` | `mattermost` | |
   | `html_context["matrix"]` | `matrix` | |
   | `html_context["github_url"]` | `github_url` | |
   | `html_context["repo_default_branch"]` | `repo_default_branch` | |
   | `html_context["repo_folder"]` | `repo_folder` | |
   | `html_context["display_contributors"]` | `display_contributors` | Boolean |

2. Also note any values in `conf.py` that are NOT covered by the template:
   - Custom Sphinx `extensions = [...]` entries beyond what the template provides
   - Extra `html_context` keys
   - Custom `html_theme_options`
   - Any other bespoke configuration

3. If the downstream repo has a `.readthedocs.yaml`, extract the RTD project
   slug for the `rtd_slug` variable.

4. Present the extracted values to the user and ask them to confirm or correct
   each one before proceeding.

### Phase 3: Identify downstream-only customizations

1. Read the downstream `docs/Makefile` and `docs/requirements.txt`.
2. Compare against the template versions (read them from the template
   directory in this repo).
3. Note any:
   - Custom Makefile targets not in the template
   - Extra Python dependencies in `requirements.txt` not in the template
   - Custom `.gitignore` entries in `docs/.gitignore`
4. Report these to the user: "These customizations will need to be re-applied
   after generation."

### Phase 4: Back up and remove overlapping files

1. Instruct the user (or perform if in the downstream workspace) to back up:

   ```bash
   mkdir /tmp/docs-backup
   cp -r docs/ /tmp/docs-backup/
   cp .readthedocs.yaml /tmp/docs-backup/ 2>/dev/null || true
   ```

2. Remove only the tooling files that overlap with the template. **CRITICAL:
   Do NOT remove documentation content files** (`.md`, `.rst`, `_static/`,
   images, custom CSS, etc.):

   ```bash
   rm -rf docs/conf.py docs/Makefile docs/requirements.txt \
          docs/.gitignore docs/_dev docs/_templates \
          docs/release-notes/template .readthedocs.yaml
   ```

3. Verify that documentation content files are still present:
   ```bash
   ls docs/*.md docs/*.rst docs/_static/ 2>/dev/null
   ```

### Phase 5: Run Copier

1. Run Copier from the downstream repo root with the confirmed values:

   ```bash
   copier copy gh:canonical/platform-engineering-documentation-files.git .
   ```

2. If running interactively, answer each prompt with the values confirmed in
   Phase 2. If running non-interactively, pass values via `--data`:

   ```bash
   copier copy --data "project=MyProject" --data "author=Canonical Ltd." ... \
     gh:canonical/platform-engineering-documentation-files.git .
   ```

3. Verify that `.copier-answers.yml` was created and contains the correct
   values.

### Phase 6: Re-apply downstream customizations

1. Diff the newly generated files against the backups:

   ```bash
   diff /tmp/docs-backup/conf.py docs/conf.py
   diff /tmp/docs-backup/Makefile docs/Makefile
   diff /tmp/docs-backup/requirements.txt docs/requirements.txt
   diff /tmp/docs-backup/.gitignore docs/.gitignore
   ```

2. For `docs/conf.py`, re-add any:
   - Custom Sphinx extensions to the `extensions` list
   - Extra `html_context` entries
   - Custom `html_theme_options`
   - Any other bespoke configuration that was in the original

3. For `docs/Makefile`, re-add any custom targets.

4. For `docs/requirements.txt`, add any extra Python dependencies.

5. For `docs/.gitignore`, merge any custom ignore patterns.

### Phase 7: Validate and commit

1. Test the build:

   ```bash
   cd docs && make html
   ```

2. If the build fails, diagnose and fix before committing. Common issues:
   - Missing custom Sphinx extensions not re-added to `requirements.txt`
   - Broken references due to changed `html_context` values
   - Missing `_static/` assets referenced in the old config

3. Once the build succeeds, instruct the user to commit:

   ```bash
   git add .
   git commit -m "Onboard documentation tooling to Copier-based management"
   ```

### Phase 8: Post-onboarding guidance

Tell the user:

- `.copier-answers.yml` is now the source of truth for project-specific
  values. **Do not edit it manually.**
- To pull in future template updates, run `copier update` from the repo root.
- To change a project value (e.g., a new Discourse URL), update
  `.copier-answers.yml` and re-run `copier update`.
- The backup at `/tmp/docs-backup/` can be deleted once everything is
  confirmed working.

## Non-Negotiables

- Never delete documentation content files (`.md`, `.rst`, `_static/`,
  images). Only remove tooling/config files that overlap with the template.
- Always back up before removing anything.
- Always confirm extracted values with the user before running Copier.
- Always test the build (`make html`) before considering the onboarding
  complete.
- Never edit `.copier-answers.yml` manually after generation.

## Template File Reference

For quick reference, these are the files the template generates and their
types:

| File | Type | Description |
|------|------|-------------|
| `docs/conf.py` | Templated | Sphinx configuration with project values |
| `docs/Makefile` | Static | Build targets (html, serve, lint, etc.) |
| `docs/requirements.txt` | Static | Python dependencies |
| `docs/.gitignore` | Static | Ignores for venv, build artifacts, node_modules |
| `docs/_dev/get_vale_conf.py` | Static | Vale configuration fetcher |
| `docs/_dev/pa11y.json` | Static | Pa11y accessibility config |
| `docs/_dev/update_sp.py` | Static | Sphinx stack updater |
| `docs/_dev/version` | Static | Tooling version marker |
| `docs/_dev/.pre-commit-config.yaml` | Static | Pre-commit hooks |
| `docs/_dev/.pymarkdown.json` | Static | PyMarkdown linter config |
| `docs/_templates/footer.html` | Static | HTML footer template |
| `docs/_templates/header.html` | Static | HTML header template |
| `docs/release-notes/template/_change-artifact-template.yaml` | Static | Change artifact template |
| `docs/release-notes/template/_release-artifact-template.yaml` | Static | Release artifact template |
| `docs/release-notes/template/release-template.rst.j2` | Static | Release note RST template |
| `.readthedocs.yaml` | Static | Read the Docs build config |
| `.copier-answers.yml` | Templated | Records Copier answers for future updates |

## Copier Question Variable Reference

Full list of variables from `copier.yml` that the user will be prompted for:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `project` | str | `"Project"` | Official project/product name |
| `author` | str | `"Canonical Ltd."` | Copyright footer author name |
| `product_page` | str | `""` | Product website URL (no `https://`) |
| `discourse` | str | `""` | Discourse instance URL |
| `mattermost` | str | `""` | Mattermost channel URL |
| `matrix` | str | `""` | Matrix channel URL |
| `github_url` | str | `""` | GitHub repo URL for "Edit on GitHub" |
| `repo_default_branch` | str | `"main"` | Default branch name |
| `repo_folder` | str | `"/docs/"` | Path to docs folder in repo |
| `ogp_image` | str | `"https://assets.ubuntu.com/v1/cc828679-docs_illustration.svg"` | Open Graph preview image |
| `html_favicon` | str | `""` | Custom favicon path |
| `product_tag` | str | `""` | Product tag image path |
| `license_name` | str | `""` | SPDX license identifier |
| `license_url` | str | `""` | License URL |
| `display_contributors` | bool | `false` | Show contributors on each page |
| `source_edit_link` | str | `""` | "Edit on GitHub" link URL |
| `rtd_slug` | str | `""` | Read the Docs project slug |
| `llms_txt_description` | str | `""` | Short description for llms.txt |