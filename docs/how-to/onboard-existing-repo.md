# How to onboard a repository with existing Sphinx Stack files

If your repository already contains unmanaged copies of files from the
Canonical Sphinx Stack, directly onboarding your repository into this
solution could result in a loss of customized components.

> **AI-assisted onboarding**: An AI agent skill is available to guide you
> through this process automatically. See
> [Skills reference](../reference/skills.md).

## Prerequisites

- Python 3.10+
- Git 2.27+
- Copier installed: `pipx install copier` or `uv tool install copier`

## Audit your existing files

Compare your repository's files against the [list of generated files](#what-gets-generated).
Any file that exists in both your repository and the template will be overwritten.

```bash
find docs/ -type f | sort
ls -la .readthedocs.yaml 2>/dev/null || echo "No .readthedocs.yaml found"
```

## Extract project-specific values

Extract values from your existing `docs/conf.py` and map them to the
corresponding Copier variables. See the [Copier variables reference](../reference/copier-answers-yml.md)
for the full list.

Pay special attention to:

- `project`, `author`, `copyright`
- All entries in `html_context` (product page, Discourse, Mattermost,
  Matrix, GitHub URL, branch, folder, product tag, contributors)
- `ogp_image`, `html_favicon`
- Any custom Sphinx extensions or configuration not covered by the template

## Identify downstream-only customizations

Find things in your current `conf.py`, `Makefile`, or `requirements.txt` that
are unique to your project and not part of the standard template. You will
re-apply these after generation.

## Back up and remove overlapping files

**Back up** your existing tooling files:

```bash
mkdir /tmp/docs-backup
cp -r docs/ /tmp/docs-backup/
cp .readthedocs.yaml /tmp/docs-backup/ 2>/dev/null || true
```

**Remove only the tooling files** that overlap with the template.
Do **not** remove your documentation content (`.md`, `.rst`, `_static/`,
images, etc.):

```bash
rm -rf docs/conf.py docs/Makefile docs/requirements.txt \
       docs/.gitignore docs/_dev docs/_templates \
       docs/release-notes/template .readthedocs.yaml
```

## Run Copier

From the root of your downstream repository:

```bash
copier copy gh:canonical/platform-engineering-documentation-files.git .
```

Copier will prompt you with the questionnaire. Use the values you extracted
in Step 2.

## Re-apply downstream customizations

Compare the newly generated files against your backup and re-apply any
project-specific changes:

```bash
diff /tmp/docs-backup/conf.py docs/conf.py
diff /tmp/docs-backup/Makefile docs/Makefile
diff /tmp/docs-backup/requirements.txt docs/requirements.txt
```

Add back any project-specific extensions, Makefile targets, or extra
Python dependencies.

## Validate and commit

Test the build:

```bash
cd docs && make html
```

If the build succeeds, proceed with committing to your repository.

## After onboarding

- Your `.copier-answers.yml` is now the source of truth for project-specific
  values. If you need to change a project value, update
  `.copier-answers.yml` and re-run `copier update`.
- To pull in future template updates, run `copier update` from the repository root.
  See [How to update a downstream repository](update-downstream-repo.md).
