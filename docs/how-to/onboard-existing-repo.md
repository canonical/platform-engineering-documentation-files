# How to onboard an existing repository

If your repository already contains unmanaged copies of the documentation
tooling files (Sphinx config, Makefile, requirements, and so on), follow this
process to bring them under Copier management.

> **AI-assisted onboarding**: An AI agent skill is available to guide you
> through this process automatically. See
> [`skills/onboard-existing-docs/SKILL.md`](../../skills/onboard-existing-docs/SKILL.md)
> for the full agent workflow.

## Prerequisites

- Python 3.10+
- Git 2.27+
- Copier installed: `pipx install copier` or `uv tool install copier`

## Step 1: Audit your existing files

Compare your repo's files against the [list of generated files](#what-gets-generated).
Any file that exists in both your repo and the template will be overwritten.

```bash
find docs/ -type f | sort
ls -la .readthedocs.yaml 2>/dev/null || echo "No .readthedocs.yaml found"
```

### What gets generated

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

## Step 2: Extract project-specific values

Extract values from your existing `docs/conf.py` and map them to the
corresponding Copier variables. See the [Copier variables reference](../reference/copier-answers-yml.md)
for the full list.

Pay special attention to:

- `project`, `author`, `copyright`
- All entries in `html_context` (product page, Discourse, Mattermost,
  Matrix, GitHub URL, branch, folder, product tag, contributors)
- `ogp_image`, `html_favicon`
- Any custom Sphinx extensions or configuration not covered by the template

## Step 3: Identify downstream-only customizations

Find things in your current `conf.py`, `Makefile`, or `requirements.txt` that
are unique to your project and not part of the standard template. You will
re-apply these after generation.

## Step 4: Back up and remove overlapping files

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

## Step 5: Run Copier

From the root of your downstream repository:

```bash
copier copy gh:canonical/platform-engineering-documentation-files.git .
```

Copier will prompt you with the questionnaire. Use the values you extracted
in Step 2.

## Step 6: Re-apply downstream customizations

Compare the newly generated files against your backup and re-apply any
project-specific changes:

```bash
diff /tmp/docs-backup/conf.py docs/conf.py
diff /tmp/docs-backup/Makefile docs/Makefile
diff /tmp/docs-backup/requirements.txt docs/requirements.txt
```

Add back any project-specific extensions, Makefile targets, or extra
Python dependencies.

## Step 7: Validate and commit

Test the build:

```bash
cd docs && make html
```

If the build succeeds, commit:

```bash
git add .
git commit -m "Onboard documentation tooling to Copier-based management"
```

## After onboarding

- Your `.copier-answers.yml` is now the source of truth for project-specific
  values. Do not edit it manually.
- To pull in future template updates, run `copier update` from the repo root.
  See [How to update a downstream repository](update-downstream-repo.md).
- If you need to change a project value (for example, a new Discourse URL), update
  `.copier-answers.yml` and re-run `copier update`.
