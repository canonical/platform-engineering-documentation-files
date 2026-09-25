---
name: phase-6-reapply-customizations
description: "Phase 6 of the onboard-existing-docs skill. Re-applies downstream customizations by diffing generated files against backups."
---

# Phase 6: Re-Apply Downstream Customizations

**Prerequisites:** Phase 5 (`phase-5-run-copier`) must be complete. Copier must have generated all files successfully.

---

## Instructions

### Step 1: Diff generated files against backups

Run diffs for each file that had downstream customizations:

```bash
diff /tmp/docs-backup/conf.py docs/conf.py
diff /tmp/docs-backup/Makefile docs/Makefile
diff /tmp/docs-backup/requirements.txt docs/requirements.txt
diff /tmp/docs-backup/.gitignore docs/.gitignore
```

### Step 2: Re-apply `conf.py` customizations

The generated `conf.py` has a `######################## Configuration extras ########################`
section at the end with commented-out scaffolds for common customizations.
**This section is added from scratch** — the generated file has no `extensions`
list, `intersphinx_mapping`, `rst_prolog`, etc. by default.

Using the `template_uncovered_values` from Phase 2, uncomment and fill in the
relevant sections. Add any additional config that doesn't fit the scaffolds.

**Do not overwrite Copier-managed values.** Only add entries that are NOT
covered by the template's Copier variables.

#### What to re-apply

| Original `conf.py` entry | Where to add it in generated `conf.py` |
|---|---|
| `extensions = [...]` | Uncomment `extensions` in the Configuration extras section |
| `intersphinx_mapping = {...}` | Uncomment `intersphinx_mapping` in the Configuration extras section |
| `rst_prolog = "..."` | Uncomment `rst_prolog` in the Configuration extras section |
| `rst_epilog = "..."` | Add `rst_epilog` after `rst_prolog` in the Configuration extras section |
| `myst_substitutions` (from YAML) | Add `import yaml` to the top of `conf.py`; add the YAML loading block after `html_context` |
| `discourse_prefix` workaround | Add the workaround block after `html_context` (see example below) |
| `redirects = {...}` (legacy) | Convert to `rediraffe_redirects` format in `redirects.txt`. Format: `<old-path> <new-path>` one per line. See example below. |
| `source_suffix = {...}` | Add `source_suffix` in the Configuration extras section |
| `exclude_patterns = [...]` | Uncomment `exclude_patterns` in the Configuration extras section |
| `html_css_files = [...]` | **Do not re-apply local paths.** The template provides remote URLs (e.g., `https://assets.ubuntu.com/v1/...`). Only re-apply entries that are custom additions NOT covered by the template defaults. |
| `html_js_files = [...]` | **Do not re-apply local paths.** The template provides remote URLs. Only re-apply entries that are custom additions NOT covered by the template defaults. |
| Extra `html_context` keys | Add to the `html_context` dict (after the license block) |
| Custom `html_theme_options` | Merge into the existing `html_theme_options` dict (or add if absent) |

#### Concrete example: typical Juju charm project

Here is what the Configuration extras section looks like after re-applying
customizations for a typical Juju charm documentation project:

```python
########################
# Configuration extras #
########################

# Custom Sphinx extensions beyond what the template provides.
extensions = [
    "sphinx.ext.intersphinx",
]

# Patterns to exclude from the build.
exclude_patterns = [
    "release-notes/index.rst",
]

# A string of reStructuredText included at the beginning of every source file.
rst_prolog = """
.. |charm| replace:: MyCharm
"""

# Intersphinx mappings for cross-referencing external documentation.
intersphinx_mapping = {
    "juju": ("https://canonical-juju.readthedocs-hosted.com/en/latest/", None),
}
```

**Important — values the template intentionally replaces:**

- **`ogp_site_url` / `html_baseurl`**: Do **not** re-apply hardcoded URLs.
  The template uses `os.environ.get("READTHEDOCS_CANONICAL_URL", "/")` which
  is the intended pattern.
- **`version` variable**: The template removes this. Only re-add it if the
  downstream project uses `version` for purposes beyond `ogp_site_url` /
  `html_baseurl`.
- **`html_css_files` / `html_js_files` with local paths**: The central
  management solution uses remote URLs for CSS and JS assets (e.g.,
  `https://assets.ubuntu.com/v1/...`). When migrating from the legacy
  `.sphinx/` layout, the old local paths (e.g., `css/pdf.css`,
  `cookie-banner.css`, `js/bundle.js`) are replaced by the template's
  remote equivalents. Do **not** carry forward the downstream's local
  paths for these — the template already includes them. Only preserve
  custom CSS/JS entries that are unique to the downstream project and
  are not provided by the template.

#### Additional examples: legacy `.sphinx/` migration

**Legacy `redirects` dict → `rediraffe_redirects`:**

If the downstream `conf.py` used `sphinx_reredirects` with a `redirects` dict:

```python
redirects = {
    'explanation/old-name': '/reference/new-name',
    'how-to/old-guide': '/how-to/new-guide',
}
```

Convert to `rediraffe_redirects` format in `redirects.txt` (one `<old-path> <new-path>` per line):

```
explanation/old-name reference/new-name
how-to/old-guide how-to/new-guide
```

> **Validate every redirect target before writing it.** Unlike
> `sphinx_reredirects`, rediraffe requires the destination to be an existing
> source file and fails the build — which runs with `--fail-on-warning`. Legacy
> starter-pack configs often carry dead redirects pointing at pages that don't
> exist in this repo (e.g. `myst-syntax-reference`, `rst-syntax-reference`).
> For each entry, confirm the source path is absent and the target file exists;
> **drop dead redirects** and flag the dropped entries in the PR description so a
> human can confirm no external inbound links relied on them.

**`rst_epilog` with `reuse/` includes:**

```python
rst_epilog = """
.. include:: /reuse/links.txt
.. include:: /reuse/substitutions.txt
"""
```

**`myst_substitutions` from YAML:**

Add `import yaml` to the top of `conf.py`, then add after `html_context`:

```python
if os.path.exists('./reuse/substitutions.yaml'):
    with open('./reuse/substitutions.yaml', 'r') as fd:
        myst_substitutions = yaml.safe_load(fd.read())
```

**`discourse_prefix` workaround:**

Add after `html_context` (before the Configuration extras section):

```python
if "discourse_prefix" not in html_context and "discourse" in html_context:
    html_context["discourse_prefix"] = html_context["discourse"] + "/t/"
```

### Step 3: Re-apply `Makefile` customizations

Using `downstream_customizations.makefile_targets` from Phase 3, re-add any custom Makefile targets. Append them after the existing targets, preserving the template's standard targets.

### Step 4: Re-apply `requirements.txt` customizations

Using `downstream_customizations.extra_dependencies` from Phase 3, add any extra Python dependencies. Append them at the end of the file with a comment:

```
# Downstream-specific dependencies
my-extra-package==1.2.3
```

### Step 5: Merge `.gitignore` customizations

Using `downstream_customizations.gitignore_patterns` from Phase 3, merge any custom ignore patterns. Append them at the end of the file with a comment:

```
# Downstream-specific ignores
my-custom-pattern/
```

### Step 5a: Restore customized release-notes templates

If `release_notes_overrides` (from Phase 1) is non-empty, reconcile the
`docs/release-notes/template/` directory:

1. **Restore customized artifact templates** from the backup so Copier's
   generated versions don't clobber downstream changes:

   ```bash
   cp /tmp/docs-backup/docs/release-notes/template/<file>.yaml \
      docs/release-notes/template/<file>.yaml
   ```

2. **Remove the format-mismatched generated file.** For a markdown workflow,
   Copier generates `release-template.rst.j2` next to the preserved
   `release-template.md.j2`; delete the generated `.rst.j2`:

   ```bash
   rm -f docs/release-notes/template/release-template.rst.j2
   ```

3. Verify the directory now contains only the intended templates:

   ```bash
   ls docs/release-notes/template/
   ```

### Step 6: Verify no content files were affected

Confirm that documentation content files from `content_files` (Phase 1) are still present and unchanged:

```bash
ls docs/*.md docs/*.rst docs/_static/ 2>/dev/null
```

### Hand-off to Phase 7

Carry forward:
- `backup_path` — from Phase 4
- `extracted_values` — from Phase 2
- `content_files` — from Phase 1