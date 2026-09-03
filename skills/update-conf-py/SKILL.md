---
name: update-conf-py
description: >
  Applies upstream canonical/sphinx-stack conf.py changes to this repository's
  templated template/docs/conf.py.jinja. Consumes the deterministic JSON report
  produced by scripts/analyze_conf_diff.py, applies high-confidence changes
  mechanically, makes judgment calls for flagged changes, respects intentional
  divergences, checks ripple effects, and writes a PR summary.
  WHEN: sphinx-stack released a new version, update conf.py.jinja from upstream,
  apply analyze_conf_diff.py report, reconcile template conf.py with sphinx-stack,
  handle conf.py sync PR.
license: Apache-2.0
metadata:
  author: Canonical/platform-engineering
  summary: Apply upstream sphinx-stack conf.py changes to the templated conf.py.jinja
  version: "1.0.0"
  tags:
    - canonical
    - platform-engineering
    - documentation
    - sphinx
    - sphinx-stack
    - conf.py
---

# Update conf.py.jinja from sphinx-stack

Deterministic first. The `scripts/analyze_conf_diff.py` script has already done
the fetching, AST diffing, divergence resolution, and ripple checks. Your job is
to apply its report to `template/docs/conf.py.jinja` and exercise judgment only
where the report asks for it.

## Description

This skill runs after `scripts/analyze_conf_diff.py` produces a JSON analysis
report comparing two upstream `canonical/sphinx-stack` `conf.py` versions. It is
invoked from the `analyze-conf-py` job in
[`.github/workflows/sphinx-stack-sync.yml`](../../.github/workflows/sphinx-stack-sync.yml)
after the verbatim-sync PR has been created.

You **propose** changes; a human **reviews and merges**. Never assume your edits
are final.

## Inputs

| Input | Source | Description |
|---|---|---|
| Analysis report | `analysis.json` from `analyze_conf_diff.py` | Structured list of upstream changes |
| Template | [`template/docs/conf.py.jinja`](../../template/docs/conf.py.jinja) | The file you edit |
| Section map | [`scripts/conf_section_map.json`](../../scripts/conf_section_map.json) | Where each config key lives in the template |
| Divergence manifest | [`scripts/conf_divergences.json`](../../scripts/conf_divergences.json) | Intentional differences from upstream |

## Report structure

The report has three top-level keys:

- `summary` — counts (`total_changes`, `actionable`, `skipped`, `auto_applicable`, `needs_llm_judgment`) plus `old_version` / `new_version`.
- `changes` — the actionable changes you must apply.
- `skipped_changes` — changes suppressed by the divergence manifest. **Do not apply these.** List them in the PR summary for human awareness only.

Each change object carries: `type`, `key`, value fields (`added`/`removed`/`old_value`/`new_value`/`changed`), `jinja_location`, optional `ripple_checks`, optional `divergence`, `confidence`, `suggested_action`, and `needs_llm`.

## Procedure

### Step 1: Triage

Split `changes` into two buckets:

- `needs_llm: false` → apply mechanically per `suggested_action` (Step 2).
- `needs_llm: true` → apply with judgment (Step 3).

Process `skipped_changes` only by summarizing them; never edit the template for them.

### Step 2: Apply mechanical changes

Use `jinja_location.line_anchor` to find the target in `template/docs/conf.py.jinja`, then apply `suggested_action`:

| `suggested_action` | How to apply |
|---|---|
| `append_to_list` | Add each item in `added` to the list at the anchor. Preserve existing ordering and any `preserve_entries` in place. |
| `remove_from_list` | Remove each item in `removed` from the list at the anchor. Never remove an item listed in `preserve_entries`. |
| `update_value` | Replace the literal value at the anchor with `new_value`. For a `copier_variable` location, do **not** hardcode the value — update the `default` in [`copier.yml`](../../copier.yml) instead (see ripple checks). |
| `add_import` | Add the import near the top of the file with the other imports. |
| `review_removal` | Do not delete outright. Treat as `needs_llm` and reason about intent (Step 3). |

### Step 3: Apply judgment changes

For `needs_llm: true` changes:

- **`new_assignment`** — Decide placement and templating:
  - Does this value vary per downstream project? If yes, it likely belongs as a **new Copier variable** in `copier.yml` plus a `{{ ... }}` reference. Flag this prominently in the PR summary — adding a Copier variable changes the questionnaire for every downstream repo and warrants explicit human sign-off.
  - If it is universal, add it verbatim to the section named in `jinja_location.section` (or a sensible new section).
- **`dict_entry_changed`** on `html_context` — Map added/changed keys through `conf_section_map.json`'s `html_context.copier_mapping`. Keys in the mapping become Copier-templated entries; unmapped keys are added as literals. Never touch keys that back existing Copier variables.
- **`extensions` additions with `ripple_checks.extensions_missing_from_requirements`** — The extension has no matching line in `requirements.txt`. Add the extension to the template's `extensions` list AND add the correct pip package to `template/docs/requirements.txt` (the module name is not always the pip name, e.g. `sphinx_tabs.tabs` → `sphinx-tabs`).
- **`jinja_location: null`** — The script could not place the change. Read the template, decide the correct section, and place it. If genuinely unclear, leave it out and flag it for the human.

### Step 4: Honor divergences

Never override `conf_divergences.json`. In particular:

- `ogp_site_url`, `html_baseurl`, `version`, `sitemap_filename` — leave the template's version untouched even if upstream changed them (these appear in `skipped_changes`).
- `html_js_files` — preserve `js/overwrite_links.js` while accepting upstream additions.
- `slug`, `html_theme_options`, `html_static_path`, `templates_path` — keep active/uncommented even though upstream comments them out.

If you add a **new** intentional divergence while resolving a change, record it in `conf_divergences.json` in the same PR so future syncs respect it.

### Step 5: Check ripple effects

For every applied change, verify the coupled files:

| Change | Coupled file to check |
|---|---|
| Extension added/removed | `template/docs/requirements.txt` |
| `copier_variable` default changed | `copier.yml` `default:` |
| New config key that could vary per project | `copier.yml` (new variable?) and `scripts/extract_conf_values.py` `uncovered_targets` |
| New list/section referenced by onboarding | `skills/onboard-existing-docs/references/phase-6-reapply-customizations.md` |

### Step 6: Validate

Run the template build to confirm the edits generate valid output:

```bash
bash tests/test_build.sh full
bash tests/test_build.sh minimal
```

Both must pass before the PR is considered ready.

### Step 7: Write the PR summary

Post a comment (or update the PR body) with this structure:

```markdown
## 🤖 conf.py.jinja analysis for sphinx-stack {new_version}

Compared upstream conf.py: {old_version} → {new_version}

### Applied automatically
| Change | Location | Action |
|---|---|---|
| ... | ... | ... |

### Applied with judgment (please review closely)
| Change | Decision | Rationale |
|---|---|---|
| ... | ... | ... |

### Skipped (intentional divergences)
| Change | Divergence rule |
|---|---|
| ... | ... |

### Requires human decision
- [ ] {e.g. "New config X could be a Copier variable — confirm before merge"}
```

## Guardrails

- You propose; the human disposes. Push edits to the sync PR branch, never merge.
- Prefer leaving a change for human review over guessing when `jinja_location` is null and intent is unclear.
- Never remove `preserve_entries` or edit anything in `skipped_changes`.
- Never hardcode a value where the template uses a Copier variable or Jinja conditional.
