#!/usr/bin/env python3
"""Extract project-specific values from a downstream docs/conf.py.

Maps each value to the corresponding Copier question variable from
platform-engineering-documentation-files/copier.yml.

Usage:
    python3 extract_conf_values.py docs/conf.py
    python3 extract_conf_values.py /path/to/downstream/docs/conf.py

Output: JSON object mapping Copier variable names to extracted values.
"""

import ast
import json
import sys
from pathlib import Path


def extract_conf_values(conf_path: str) -> dict:
    """Parse a Sphinx conf.py and extract values mapped to Copier variables."""
    with open(conf_path, "r") as f:
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

    # ── Walk the AST ───────────────────────────────────────────
    for node in ast.walk(tree):
        # Top-level assignments: project = "...", author = "...", etc.
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in top_level_targets:
                    value = _literal_value(node.value)
                    if value is not None:
                        result[top_level_targets[target.id]] = value

        # html_context = {...} dictionary
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "html_context":
                    if isinstance(node.value, ast.Dict):
                        for key, val in zip(node.value.keys, node.value.values):
                            key_str = _literal_value(key)
                            if key_str in html_context_targets:
                                value = _literal_value(val)
                                if value is not None:
                                    result[html_context_targets[key_str]] = value

    return result


def _literal_value(node: ast.expr):
    """Safely extract a literal value from an AST node."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in ("True", "False"):
        return node.id == "True"
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        if isinstance(node.operand, ast.Constant):
            return -node.operand.value
    # Joined strings (f-strings) — return as string representation
    if isinstance(node, ast.JoinedStr):
        parts = []
        for val in node.values:
            if isinstance(val, ast.Constant):
                parts.append(str(val.value))
            elif isinstance(val, ast.FormattedValue):
                parts.append("{...}")
        return "".join(parts)
    return None


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