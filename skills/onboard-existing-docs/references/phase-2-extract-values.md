---
name: phase-2-extract-values
description: "Phase 2 of the onboard-existing-docs skill. Extracts project-specific values from the downstream conf.py and maps them to Copier variables."
---

# Phase 2: Extract Project-Specific Values

**Prerequisites:** Phase 1 (`phase-1-audit`) must be complete. You should already have the `overlapping_files` list.

---

## Instructions

### Step 1: Run the extraction script

Run the automated extraction script to parse the downstream `docs/conf.py`:

```bash
python3 scripts/extract_conf_values.py docs/conf.py
```

This outputs a JSON object with two keys:

- `copier_values` — Copier variable → extracted value (for `extracted_values`)
- `template_uncovered` — config NOT covered by the template (for `template_uncovered_values`)

If the script cannot be run (e.g., the downstream repo doesn't have Python available), proceed with manual extraction in Step 2.

### Step 1a: Extract domain redirect values from `overwrite_links.js`

`overwrite_links.js` may live in either the new `_dev/` layout or the legacy
`.sphinx/` layout. Check both locations:

```bash
# Check new layout first, then legacy
for path in docs/_static/js/overwrite_links.js docs/.sphinx/_static/js/overwrite_links.js; do
  if test -f "$path"; then
    grep -oP "const oldDomain = '\\K[^']+" "$path" 2>/dev/null || echo ""
    grep -oP "const newDomain = '\\K[^']+" "$path" 2>/dev/null || echo ""
    break
  fi
done
```

Map the results to `extracted_values`:
- `old_domain` — the extracted `oldDomain` value (empty string if not found)
- `new_domain` — the extracted `newDomain` value (empty string if not found)

If neither file exists or the grep returns empty, leave both as empty
strings (the Copier defaults).

### Step 2: Manual extraction (fallback)

If the script is unavailable, manually read `docs/conf.py` and extract each value. Map to the corresponding Copier question variable:

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
| `overwrite_links.js`: `const oldDomain = '...'` | `old_domain` | Old RTD domain to redirect from |
| `overwrite_links.js`: `const newDomain = '...'` | `new_domain` | New canonical.com domain path |

### Step 3: Identify values NOT covered by the template

The extraction script's `template_uncovered` output already captures most non-Copier config. Review it and supplement with manual inspection for any additional values.

Common non-Copier config to look for:
- Custom Sphinx `extensions = [...]` entries beyond what the template provides
- `intersphinx_mapping` for cross-referencing external docs
- `rst_prolog` with custom substitutions (e.g., `|charm|`)
- `rst_epilog` with `.. include::` directives (e.g., `reuse/links.txt`)
- `myst_substitutions` loaded from YAML (e.g., `reuse/substitutions.yaml`)
- `redirects = {...}` (legacy `sphinx_reredirects` dict) — modernize to `rediraffe_redirects` in Phase 6
- `discourse_prefix` workaround for canonical-sphinx issue #34
- `exclude_patterns`, `html_css_files`, `html_js_files`
- `html_static_path`, `templates_path`
- `linkcheck_retries`, `linkcheck_timeout`
- `sitemap_filename`
- Extra `html_context` keys not covered by Copier variables
- Custom `html_theme_options`

These will be re-applied in Phase 6.

**Important — values the template intentionally replaces:**

- **`ogp_site_url` / `html_baseurl`**: The template replaces hardcoded URLs with `os.environ.get("READTHEDOCS_CANONICAL_URL", "/")`. Do **not** preserve the original hardcoded values — the template's environment-variable-based lookup is the intended pattern.
- **`version` variable**: The template removes the `version = f"{os.environ.get('READTHEDOCS_VERSION', 'local')}"` pattern. If the downstream project uses `version` for purposes beyond `ogp_site_url`/`html_baseurl`, flag it as a customization to re-apply.

### Step 4: Extract RTD slug (if applicable)

Extract the `rtd_slug` Copier variable. **`rtd_slug` is the URL path segment used
to build the canonical docs URL, not necessarily the Read the Docs project slug.**
The template renders it as `https://canonical.com/{{ rtd_slug }}/{version}/`, so it
must match the path in the existing `html_baseurl` / `ogp_site_url`, not the RTD
dashboard project name.

To find the right value, check these sources in order:

- The existing `conf.py` `slug = "..."` value, or the path in
  `ogp_site_url` / `html_baseurl` (e.g. `https://canonical.com/juju/docs/haproxy-charm/...`
  → `rtd_slug = "juju/docs/haproxy-charm"`).
- The `new_domain` from `overwrite_links.js` (the path after the host).

The RTD *project* slug (e.g. `canonical-haproxy-juju-charm`, often visible in
`old_domain`) is usually **not** the correct value — do not use it unless it
matches the canonical URL path.

### Step 5: Confirm values with the user

Present the extracted values to the user using the question bank (see [`question-bank.md`](question-bank.md), Section "Confirm Extracted Values"). Ask them to confirm or correct each one before proceeding.

Do not proceed to Phase 3 until the user has confirmed all values.

### Hand-off to Phase 3

Carry forward:
- `extracted_values` — dict of Copier variable → confirmed value
- `template_uncovered_values` — list of custom config not covered by the template
- `overlapping_files` — from Phase 1
- `content_files` — from Phase 1