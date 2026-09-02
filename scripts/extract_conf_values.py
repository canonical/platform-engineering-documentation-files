#!/usr/bin/env python3
"""Extract project-specific values from a downstream docs/conf.py.

Maps each value to the corresponding Copier question variable from
platform-engineering-documentation-files/copier.yml, and also extracts
non-Copier config values (extensions, intersphinx_mapping, etc.) that
need to be re-applied during onboarding.

Usage:
    python3 scripts/extract_conf_values.py docs/conf.py
    python3 scripts/extract_conf_values.py /path/to/downstream/docs/conf.py

Output: JSON object with two keys:
    "copier_values"       — Copier variable → extracted value
    "template_uncovered"  — config not covered by the template
"""

import ast
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _conf_ast import extract_any_value, literal_value  # noqa: E402


def extract_conf_values(conf_path: str) -> dict:
    """Parse a Sphinx conf.py and extract values mapped to Copier variables."""
    with open(conf_path) as f:
        source = f.read()

    tree = ast.parse(source)

    result: dict = {}

    # ── Top-level assignments ──────────────────────────────────
    top_level_targets = {
        "project": "project",
        "author": "author",
        "ogp_image": "ogp_image",
        "html_favicon": "html_favicon",
        "html_title": "html_title",
    }

    # ── html_context dictionary entries ────────────────────────
    html_context_targets = {
        "product_page": "product_page",
        "product_tag": "product_tag",
        "discourse": "discourse",
        "mattermost": "mattermost",
        "matrix": "matrix",
        "github_url": "github_url",
        "repo_default_branch": "repo_default_branch",
        "repo_folder": "repo_folder",
        "display_contributors": "display_contributors",
    }

    # ── Non-Copier config (re-applied in Phase 6) ──────────────
    # These are configuration values NOT covered by the template
    # but that the downstream project may have customized.
    uncovered_targets = {
        "extensions",
        "intersphinx_mapping",
        "rst_prolog",
        "exclude_patterns",
        "html_css_files",
        "html_js_files",
        "html_static_path",
        "templates_path",
        "linkcheck_retries",
        "linkcheck_timeout",
        "sitemap_filename",
        "html_extra_path",
        "numfig",
        "nitpick_ignore",
        "nitpick_ignore_regex",
        "suppress_warnings",
    }

    uncovered: dict = {}  # Non-Copier config values

    # ── Walk the AST ───────────────────────────────────────────
    for node in ast.walk(tree):
        # Top-level assignments: project = "...", author = "...", etc.
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in top_level_targets:
                    value = literal_value(node.value)
                    if value is not None:
                        result[top_level_targets[target.id]] = value

                # Non-Copier top-level assignments
                if isinstance(target, ast.Name) and target.id in uncovered_targets:
                    value = extract_any_value(node.value)
                    if value is not None:
                        uncovered[target.id] = value

        # html_context = {...} dictionary
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "html_context":
                    if isinstance(node.value, ast.Dict):
                        for key, val in zip(node.value.keys, node.value.values):
                            key_str = literal_value(key)
                            if key_str in html_context_targets:
                                value = literal_value(val)
                                if value is not None:
                                    result[html_context_targets[key_str]] = value

    return {"copier_values": result, "template_uncovered": uncovered}


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path/to/conf.py>", file=sys.stderr)
        sys.exit(1)

    conf_path = Path(sys.argv[1])
    if not conf_path.exists():
        print(f"Error: {conf_path} not found", file=sys.stderr)
        sys.exit(1)

    values = extract_conf_values(str(conf_path))
    print(json.dumps(values, indent=2))


if __name__ == "__main__":
    main()
