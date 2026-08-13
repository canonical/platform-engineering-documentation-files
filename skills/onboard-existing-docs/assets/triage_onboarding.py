#!/usr/bin/env python3
"""Triage script for onboarding a downstream repo to the Platform Engineering
documentation files template.

Compares each file in the downstream repository against the template and
produces a structured JSON report classifying each file by effort level.

Usage:
    python triage_onboarding.py --repo-path /path/to/downstream/repo
    python triage_onboarding.py --repo-path /path/to/downstream/repo --template-path /path/to/template
"""

import argparse
import difflib
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Manifest of all template files
# ---------------------------------------------------------------------------
# Each entry: (relative_path_from_template_root, is_templated)
# Paths are relative to the {{cookiecutter.project_name}}/ directory.

TEMPLATE_MANIFEST: List[Tuple[str, bool]] = [
    # Root-level files
    (".readthedocs.yaml", False),
    # docs/ files
    ("docs/conf.py", True),
    ("docs/Makefile", False),
    ("docs/requirements.txt", False),
    ("docs/.gitignore", False),
    # docs/_dev/ files
    ("docs/_dev/get_vale_conf.py", False),
    ("docs/_dev/update_sp.py", False),
    ("docs/_dev/pa11y.json", False),
    ("docs/_dev/.pre-commit-config.yaml", False),
    ("docs/_dev/.pymarkdown.json", False),
    ("docs/_dev/version", False),
    # docs/_templates/ files
    ("docs/_templates/footer.html", False),
    ("docs/_templates/header.html", False),
    # docs/release-notes/template/ files
    ("docs/release-notes/template/_change-artifact-template.yaml", False),
    ("docs/release-notes/template/_release-artifact-template.yaml", False),
    ("docs/release-notes/template/release-template.rst.j2", False),
]

# Directories that contain template-managed files (used for extra-file detection)
TEMPLATE_DIRS = [
    "",
    "docs",
    "docs/_dev",
    "docs/_templates",
    "docs/release-notes/template",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINOR_DIFF_THRESHOLD = 5


def discover_template_root(script_dir: str) -> str:
    """Auto-discover the template root from the script's location.

    The script lives at: skills/onboard-existing-docs/assets/triage_onboarding.py
    The template root (containing {{cookiecutter.project_name}}/) is 3 levels up.
    """
    return os.path.abspath(os.path.join(script_dir, "..", "..", ".."))


def read_file_safe(path: str) -> Optional[str]:
    """Read a file as text, returning None if it doesn't exist or is binary."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (UnicodeDecodeError, OSError):
        return None


def count_diff_lines(template_text: str, downstream_text: str) -> int:
    """Count the number of changed lines in a unified diff."""
    diff = list(
        difflib.unified_diff(
            template_text.splitlines(keepends=True),
            downstream_text.splitlines(keepends=True),
            fromfile="template",
            tofile="downstream",
        )
    )
    # Count lines that start with + or - but not the header lines (---, +++, @@)
    changed = 0
    for line in diff:
        if line.startswith(("+", "-")) and not line.startswith(("---", "+++")):
            changed += 1
    return changed


def classify_verbatim_file(
    template_path: str, downstream_path: str
) -> Dict[str, Any]:
    """Classify a single verbatim file by comparing template vs downstream."""
    template_text = read_file_safe(template_path)
    downstream_text = read_file_safe(downstream_path)

    if template_text is None:
        return {
            "status": "error",
            "diff_lines": 0,
            "note": "Template file could not be read.",
        }

    if downstream_text is None:
        return {
            "status": "missing",
            "diff_lines": 0,
            "note": "File does not exist in the downstream repository.",
        }

    if template_text == downstream_text:
        return {
            "status": "identical",
            "diff_lines": 0,
            "note": "File is identical to the template.",
        }

    diff_lines = count_diff_lines(template_text, downstream_text)
    if diff_lines <= MINOR_DIFF_THRESHOLD:
        return {
            "status": "minor_diff",
            "diff_lines": diff_lines,
            "note": (
                f"File differs from the template by {diff_lines} changed lines "
                f"(≤ {MINOR_DIFF_THRESHOLD}). Likely version bumps or minor tweaks."
            ),
        }
    else:
        return {
            "status": "major_diff",
            "diff_lines": diff_lines,
            "note": (
                f"File differs from the template by {diff_lines} changed lines "
                f"(> {MINOR_DIFF_THRESHOLD}). Likely significant customization."
            ),
        }


def detect_extra_files(
    repo_path: str, manifest_paths: set
) -> List[str]:
    """Detect files in the downstream repo under template-managed directories
    that are not part of the template manifest."""
    extras: List[str] = []
    for dir_name in TEMPLATE_DIRS:
        scan_dir = os.path.join(repo_path, dir_name) if dir_name else repo_path
        if not os.path.isdir(scan_dir):
            continue
        for entry in sorted(os.listdir(scan_dir)):
            full_path = os.path.join(scan_dir, entry)
            if not os.path.isfile(full_path):
                continue
            rel_path = (
                os.path.join(dir_name, entry) if dir_name else entry
            )
            if rel_path not in manifest_paths:
                extras.append(rel_path)
    return extras


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run(repo_path: str, template_root: str) -> Dict[str, Any]:
    """Run the full triage and return a report dictionary."""
    # Normalise paths
    repo_path = os.path.abspath(repo_path)
    template_root = os.path.abspath(template_root)

    if not os.path.isdir(repo_path):
        print(f"Error: repo path does not exist or is not a directory: {repo_path}", file=sys.stderr)
        sys.exit(1)

    # The template files live under {{cookiecutter.project_name}}/ inside template_root
    template_files_dir = os.path.join(template_root, "{{cookiecutter.project_name}}")
    if not os.path.isdir(template_files_dir):
        print(f"Error: template files directory not found: {template_files_dir}", file=sys.stderr)
        sys.exit(1)

    manifest_paths = {path for path, _ in TEMPLATE_MANIFEST}

    # Classify each file
    results: List[Dict[str, Any]] = []
    summary = {
        "identical": 0,
        "minor_diff": 0,
        "major_diff": 0,
        "missing": 0,
        "templated_needs_manual": 0,
        "error": 0,
    }

    for rel_path, is_templated in TEMPLATE_MANIFEST:
        template_path = os.path.join(template_files_dir, rel_path)
        downstream_path = os.path.join(repo_path, rel_path)

        if is_templated:
            # conf.py is always templated — needs manual mapping
            entry: Dict[str, Any] = {
                "path": rel_path,
                "status": "templated_needs_manual",
                "diff_lines": 0,
                "note": (
                    "This file is templatized with ~20 cookiecutter variables. "
                    "Values must be manually extracted from the downstream version "
                    "and mapped to template variables."
                ),
            }
            summary["templated_needs_manual"] += 1
        else:
            entry = {"path": rel_path}
            classification = classify_verbatim_file(template_path, downstream_path)
            entry.update(classification)
            status = entry["status"]
            if status in summary:
                summary[status] += 1

        results.append(entry)

    # Detect extra files
    extras = detect_extra_files(repo_path, manifest_paths)

    return {
        "repo_path": repo_path,
        "template_root": template_root,
        "summary": summary,
        "files": results,
        "extras": extras,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Triage a downstream repo for onboarding to the Platform "
        "Engineering documentation files template."
    )
    parser.add_argument(
        "--repo-path",
        required=True,
        help="Path to the downstream repository to assess.",
    )
    parser.add_argument(
        "--template-path",
        default=None,
        help=(
            "Path to the template repository root (the directory containing "
            "cookiecutter.json). Auto-discovered from the script location if omitted."
        ),
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print the JSON output (default).",
    )
    parser.add_argument(
        "--no-pretty",
        action="store_false",
        dest="pretty",
        help="Output compact JSON.",
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_root = args.template_path or discover_template_root(script_dir)

    report = run(args.repo_path, template_root)

    indent = 2 if args.pretty else None
    print(json.dumps(report, indent=indent))


if __name__ == "__main__":
    main()