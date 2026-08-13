---
name: resolve-conf-py
description: "Phase 2 of the onboard-existing-docs skill. Reads the downstream conf.py, extracts hardcoded values, maps them to the ~20 cookiecutter template variables, and confirms the mapping with the user."
---

# resolve-conf-py

**Prerequisites:** This is Phase 2 of the `onboard-existing-docs` skill.
Phase 1 (`triage-and-preflight.md`) must be completed first. You need:
- `repo_path` — absolute path to the downstream repository
- `triage_report` — the JSON report from the triage script

---

## Instructions

### Step 1: Read the downstream conf.py

Read the downstream `docs/conf.py`:

```
Read the file at <repo_path>/docs/conf.py
```

Also read the template's `conf.py` for reference:

```
Read the file at <template_root>/{{cookiecutter.project_name}}/docs/conf.py
```

The template `conf.py` contains Jinja2 template tags like
`{{ cookiecutter.project_name }}` and conditional blocks like
`{% if cookiecutter.html_favicon %}...{% endif %}`.

### Step 2: Extract values from the downstream conf.py

For each template variable below, locate the corresponding value in the
downstream `conf.py` and extract it. Present your findings as a mapping table.

#### Template variable mapping table

| # | Template variable | Where to find in downstream conf.py | Downstream value |
|---|---|---|---|
| 1 | `project_name` | `project = "..."` | *(extract)* |
| 2 | `author` | `author = "..."` | *(extract)* |
| 3 | `product_page` | `html_context["product_page"]` | *(extract)* |
| 4 | `discourse` | `html_context["discourse"]` | *(extract)* |
| 5 | `mattermost` | `html_context["mattermost"]` | *(extract)* |
| 6 | `matrix` | `html_context["matrix"]` | *(extract)* |
| 7 | `github_url` | `html_context["github_url"]` | *(extract)* |
| 8 | `repo_default_branch` | `html_context["repo_default_branch"]` | *(extract)* |
| 9 | `repo_folder` | `html_context["repo_folder"]` | *(extract)* |
| 10 | `display_contributors` | `html_context["display_contributors"]` | *(extract)* |
| 11 | `license_name` | `html_context["license"]["name"]` | *(extract)* |
| 12 | `license_url` | `html_context["license"]["url"]` | *(extract)* |
| 13 | `ogp_site_name` | `ogp_site_name = "..."` | *(extract)* |
| 14 | `ogp_image` | `ogp_image = "..."` | *(extract)* |
| 15 | `html_favicon` | `html_favicon = "..."` (may be absent) | *(extract or "not set")* |
| 16 | `product_tag` | `html_context["product_tag"]` (may be absent) | *(extract or "not set")* |
| 17 | `sequential_nav` | `html_context["sequential_nav"]` (may be absent) | *(extract or "not set")* |
| 18 | `source_edit_link` | `html_theme_options["source_edit_link"]` (may be absent) | *(extract or "not set")* |
| 19 | `slug` | `slug = "..."` (may be absent) | *(extract or "not set")* |
| 20 | `llms_txt_description` | *(may not exist in downstream)* | *(extract or "not set")* |
| 21 | `manpages_url` | *(may not exist in downstream)* | *(extract or "not set")* |
| 22 | `disable_feedback_button` | *(may not exist in downstream)* | *(extract or "not set")* |

#### Extraction guidance

- **String values**: Extract the exact string between the quotes. Do not
  include the quotes themselves.
- **Boolean values**: `display_contributors` and `disable_feedback_button` are
  booleans. In the downstream `conf.py` they may be `True`/`False` (Python) or
  `"True"`/`"False"` (strings). The template expects `True` or `False` (Python
  booleans).
- **Absent values**: If a variable does not appear in the downstream `conf.py`,
  mark it as "not set". The template will use its default (usually empty string
  or `False`).
- **Conditional blocks**: Some variables control conditional blocks in the
  template (e.g., `html_favicon`, `product_tag`, `sequential_nav`,
  `source_edit_link`, `slug`). If the downstream `conf.py` has the
  corresponding code present, the variable should be set. If the code is
  absent, the variable should be left empty/unset.

### Step 3: Present the mapping table to the user

Show the completed mapping table to the user. Ask them to review each value
carefully — incorrect mappings will cause broken documentation builds (wrong
URLs, missing favicon, broken navigation, etc.).

Ask: **"Do these extracted values look correct? Would you like to change any?"**

If the user wants changes, update the table and re-confirm.

### Step 4: Update .cruft.json with the template variables

The `.cruft.json` file in the downstream repository contains a `context` field
that holds the cookiecutter variable values. Update it with the confirmed
mappings.

Read the current `.cruft.json`:

```
Read <repo_path>/.cruft.json
```

Update the `context` field with the confirmed values. The context should be a
JSON object with keys matching the `cookiecutter.json` variable names:

```json
{
  "context": {
    "project_name": "<value from mapping #1>",
    "author": "<value from mapping #2>",
    "product_page": "<value from mapping #3>",
    "discourse": "<value from mapping #4>",
    "mattermost": "<value from mapping #5>",
    "matrix": "<value from mapping #6>",
    "github_url": "<value from mapping #7>",
    "repo_default_branch": "<value from mapping #8>",
    "repo_folder": "<value from mapping #9>",
    "display_contributors": "<value from mapping #10>",
    "license_name": "<value from mapping #11>",
    "license_url": "<value from mapping #12>",
    "ogp_site_name": "<value from mapping #13>",
    "ogp_image": "<value from mapping #14>",
    "html_favicon": "<value from mapping #15>",
    "product_tag": "<value from mapping #16>",
    "sequential_nav": "<value from mapping #17>",
    "source_edit_link": "<value from mapping #18>",
    "slug": "<value from mapping #19>",
    "llms_txt_description": "<value from mapping #20>",
    "manpages_url": "<value from mapping #21>",
    "disable_feedback_button": "<value from mapping #22>"
  }
}
```

**Important:** Only include the `context` field update. Do not modify the
`template`, `commit`, or other fields in `.cruft.json`.

Write the updated `.cruft.json` back to the downstream repository.

### Step 5: Run cruft update to apply the template

Now that the context is populated, run `cruft update` to apply the template
with the confirmed variables:

```bash
cd <repo_path>
cruft update
```

**What this does:** `cruft update` diffs the current state of the downstream
files against the template and presents changes interactively. Since the
context is now populated, `docs/conf.py` will be rendered with the correct
values.

**Handle the interactive prompts:**
- For `docs/conf.py`: review the rendered version. It should match the
  downstream version closely (since we extracted the values from it). Accept
  the changes.
- For verbatim files that were `identical` in the triage: accept (no actual
  changes).
- For verbatim files that were `minor_diff` or `major_diff`: **skip for now**.
  These will be handled in Phase 3.
- For `missing` files: accept (cruft will create them).

**If cruft shows unexpected diffs in `docs/conf.py`:** The extracted values may
not match perfectly. Review the diff carefully. If the rendered version is
correct, accept it. If the downstream version has customizations not covered by
template variables, note them — they may need to be preserved via the skip list
or manual merge.

### Step 6: Hand off to Phase 3

Record the following:
- The confirmed variable mappings (for reference in Phase 3)
- Any `docs/conf.py` customizations that couldn't be captured by template
  variables

Proceed to [`handle-diffs-and-verify.md`](handle-diffs-and-verify.md).