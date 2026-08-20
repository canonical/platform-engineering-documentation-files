# Onboard-Existing-Docs Skill: Experience Report

## Overview

Used the `onboard-existing-docs` skill to onboard `testing-onboarding-discourse-k8s` into the Copier-based platform-engineering-documentation-files management solution. The process completed successfully with a clean build (zero warnings).

## What went smoothly

- **Phase structure is clear and logical.** The eight-phase breakdown with explicit hand-off state made it easy to track progress and know what to carry forward.
- **The extraction script worked perfectly.** `extract_conf_values.py` parsed the downstream `conf.py` via AST and produced accurate JSON output, saving significant manual effort.
- **The overlapping file list in Phase 1 was accurate.** The table mapping template sources to downstream outputs made identification straightforward.
- **Phase 3 (identify customizations) was efficient.** Comparing downstream vs template Makefile/requirements/gitignore revealed they were identical, which the skill correctly anticipated as a possible outcome.
- **The build succeeded on the first attempt after Phase 6.** This validates that the re-application logic was sound.

## What was confusing or challenging

- **The `display_contributors` boolean rendered as `false` (JavaScript-style) instead of `False` (Python).** The Jinja template uses `{{ display_contributors|lower }}`, which produces the string `false` — invalid Python syntax. I had to fix this manually. This is a bug in the template itself (`conf.py.jinja`), not the skill, but the skill doesn't warn about it.

- **Phase 6 is underspecified for `conf.py` customizations.** The instruction says "re-add any custom Sphinx extensions to the `extensions` list" but the generated `conf.py` has no `extensions` list at all — there's no section to append to. The skill could clarify that the entire `######################## Configuration extras ########################` section (extensions, exclude_patterns, html_css/js_files, rst_prolog, intersphinx_mapping) needs to be added from scratch rather than "re-applied."

- **Ambiguity about what counts as a "Copier-managed value" vs a "customization."** Some things in the original conf.py (like `sitemap_filename`, `linkcheck_retries`, `html_static_path`/`templates_path`) are neither Copier variables nor clearly "custom extensions." The skill could provide a clearer decision framework for borderline config entries.

- **The `ogp_site_url` and `html_baseurl` values changed semantics.** The original used hardcoded URLs with a version variable; the template uses `os.environ.get("READTHEDOCS_CANONICAL_URL", "/")`. This is arguably an improvement, but the skill doesn't explicitly call out that the template intentionally replaces certain patterns with better alternatives, so there's a moment of uncertainty about whether to preserve the original or accept the template's version.

- **No guidance on the `version` variable.** The original conf.py defined `version = f"{os.environ.get('READTHEDOCS_VERSION', 'local')}"` which was used in `ogp_site_url` and `html_baseurl`. The template removes this entirely. The skill doesn't mention this common pattern or advise whether to keep it.

## Recommendations

1. **Fix the template bug:** Change `{{ display_contributors|lower }}` in `conf.py.jinja` to `{{ display_contributors }}` (Jinja renders Python booleans as `True`/`False` by default) or use a custom filter.

2. **Add a "Configuration extras" scaffold to the template.** Even if just a commented-out `extensions = [...]` section, this would give Phase 6 a clear insertion point and reduce ambiguity.

3. **Phase 6 could include a concrete example** showing what a fully re-applied `conf.py` looks like for a typical Juju charm project (extensions list, intersphinx, rst_prolog, etc.). The current instructions are procedural but lack a "what the result should look like" reference.

4. **Phase 2 could flag values that the template intentionally replaces.** A short note like "The template replaces hardcoded `ogp_site_url`/`html_baseurl` with environment-variable-based lookups — do not preserve the original hardcoded values" would save decision time.

5. **The extraction script could also extract non-Copier values.** Adding a second output section for "uncovered config" (extensions, intersphinx_mapping, rst_prolog, etc.) would make Phase 6 more mechanical and less reliant on manual conf.py reading.

6. **Phase 5 could note that `copier copy` with `--defaults --overwrite` is the recommended non-interactive approach.** The current instructions show `--data` flags but don't mention `--defaults` (to skip prompts for unspecified values) or `--overwrite` (needed when docs/ directory already has content files).