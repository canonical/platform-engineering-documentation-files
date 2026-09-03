#!/usr/bin/env python3
"""Analyze the diff between two upstream sphinx-stack ``conf.py`` versions.

Produces a structured JSON report describing what changed upstream, where each
change maps into ``template/docs/conf.py.jinja``, whether the change collides
with an intentional divergence, and any ripple effects on ``requirements.txt``
or ``copier.yml``. The report is designed to be consumed by an LLM agent (see
``skills/update-conf-py/SKILL.md``) that applies the changes to the template.

The script itself performs only deterministic work: fetching, AST parsing,
structural diffing, divergence resolution, and ripple checks. Judgment calls
are deferred to the agent by flagging changes with ``"needs_llm": true``.

Usage:
    python3 scripts/analyze_conf_diff.py \
        --old-upstream https://raw.githubusercontent.com/canonical/sphinx-stack/v2.0.0/docs/conf.py \
        --new-upstream https://raw.githubusercontent.com/canonical/sphinx-stack/v2.1.0/docs/conf.py \
        --section-map scripts/conf_section_map.json \
        --divergences scripts/conf_divergences.json \
        --requirements template/docs/requirements.txt \
        --copier copier.yml \
        --output analysis.json

Both ``--old-upstream`` and ``--new-upstream`` accept either an ``http(s)://``
URL or a local filesystem path.
"""

import argparse
import ast
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _conf_ast import imports, top_level_assignments  # noqa: E402


def load_source(location: str) -> str:
    """Read conf.py source from a URL or a local path."""
    if location.startswith("http://") or location.startswith("https://"):
        with urllib.request.urlopen(location, timeout=30) as resp:  # noqa: S310
            return resp.read().decode("utf-8")
    return Path(location).read_text(encoding="utf-8")


def parse(source: str) -> ast.Module:
    return ast.parse(source)


def diff_assignments(old: dict, new: dict) -> list:
    """Compute a structural diff between two ``name -> value`` mappings."""
    changes: list = []
    keys = sorted(set(old) | set(new))

    for key in keys:
        in_old = key in old
        in_new = key in new

        if not in_old and in_new:
            changes.append({"type": "new_assignment", "key": key, "new_value": new[key]})
        elif in_old and not in_new:
            changes.append({"type": "removed_assignment", "key": key, "old_value": old[key]})
        elif old[key] != new[key]:
            changes.extend(_diff_value(key, old[key], new[key]))

    return changes


def _diff_value(key: str, old_val, new_val) -> list:
    """Diff a single key whose value changed, specializing lists and dicts."""
    if isinstance(old_val, list) and isinstance(new_val, list):
        added = [item for item in new_val if item not in old_val]
        removed = [item for item in old_val if item not in new_val]
        result = []
        if added:
            result.append({"type": "list_item_added", "key": key, "added": added})
        if removed:
            result.append({"type": "list_item_removed", "key": key, "removed": removed})
        return result

    if isinstance(old_val, dict) and isinstance(new_val, dict):
        added = {k: v for k, v in new_val.items() if k not in old_val}
        removed = {k: v for k, v in old_val.items() if k not in new_val}
        changed = {
            k: {"old": old_val[k], "new": new_val[k]}
            for k in new_val
            if k in old_val and old_val[k] != new_val[k]
        }
        return [
            {
                "type": "dict_entry_changed",
                "key": key,
                "added": added,
                "removed": removed,
                "changed": changed,
            }
        ]

    return [
        {
            "type": "value_changed",
            "key": key,
            "old_value": old_val,
            "new_value": new_val,
        }
    ]


def diff_imports(old_tree: ast.Module, new_tree: ast.Module) -> list:
    old_imports = set(imports(old_tree))
    new_imports = set(imports(new_tree))
    changes = []
    for name in sorted(new_imports - old_imports):
        changes.append({"type": "import_added", "key": name})
    for name in sorted(old_imports - new_imports):
        changes.append({"type": "import_removed", "key": name})
    return changes


def _candidate_pip_names(extension: str) -> list:
    """Heuristic pip package names for a Sphinx extension module name."""
    base = extension.split(".")[0]
    candidates = {
        extension.replace("_", "-").replace(".", "-"),
        base.replace("_", "-"),
    }
    return sorted(candidates)


def _requirements_has(extension: str, requirements_lines: list) -> bool:
    normalized = [line.strip().lower() for line in requirements_lines]
    for candidate in _candidate_pip_names(extension):
        for line in normalized:
            if line.startswith(candidate.lower()):
                return True
    return False


def _copier_default(copier_data: dict, copier_key: str):
    entry = copier_data.get(copier_key)
    if isinstance(entry, dict):
        return entry.get("default")
    return None


def resolve_divergence(change: dict, divergences: dict) -> dict:
    """Apply the divergence manifest to a single change, mutating it in place."""
    key = change["key"]
    divergence = divergences.get(key)
    if not divergence:
        return change

    change["divergence"] = {
        "type": divergence["type"],
        "rule": divergence["rule"],
        "rationale": divergence.get("rationale", ""),
    }
    rule = divergence["rule"]

    if rule == "ignore_upstream_changes":
        change["suggested_action"] = "skip"
        change["needs_llm"] = False
        change["confidence"] = "high"
        change["note"] = (
            f"'{key}' is an intentional divergence "
            f"({divergence['type']}); upstream change ignored."
        )
    elif rule == "merge_upstream_changes_preserve_custom":
        custom = divergence.get("custom_entries", [])
        if change["type"] == "list_item_removed":
            change["removed"] = [item for item in change.get("removed", []) if item not in custom]
            if not change["removed"]:
                change["suggested_action"] = "skip"
                change["note"] = (
                    f"Only custom entries would be removed from '{key}'; preserving them."
                )
        change.setdefault("preserve_entries", custom)
    elif rule == "keep_active":
        change["note"] = (
            f"'{key}' is kept active in the template even though upstream "
            f"comments it out; keep it uncommented when applying."
        )

    return change


def enrich(change: dict, section_map: dict, requirements_lines: list, copier_data: dict) -> dict:
    """Attach jinja_location, ripple_checks, and default confidence."""
    key = change["key"]
    section = section_map.get(key)

    if section:
        change["jinja_location"] = {
            "section": section["jinja_section"],
            "line_anchor": section["line_anchor"],
            "type": section["type"],
        }
        if section.get("copier_key"):
            change["jinja_location"]["copier_key"] = section["copier_key"]
    else:
        change["jinja_location"] = None

    ripple: dict = {}

    # Ripple: new extensions must have a matching requirement.
    if key == "extensions" and change["type"] == "list_item_added":
        missing = [
            ext
            for ext in change.get("added", [])
            if not _requirements_has(ext, requirements_lines)
        ]
        ripple["extensions_missing_from_requirements"] = missing
        if missing:
            change["needs_llm"] = True
            change["confidence"] = "medium"

    # Ripple: copier-mapped value change may need a copier.yml default update.
    if section and section.get("type") == "copier_variable" and change["type"] == "value_changed":
        copier_key = section.get("copier_key")
        current_default = _copier_default(copier_data, copier_key)
        mismatch = current_default != change.get("new_value")
        ripple["copier_default_mismatch"] = mismatch
        ripple["current_copier_default"] = current_default
        ripple["copier_key"] = copier_key

    if ripple:
        change["ripple_checks"] = ripple

    # Defaults for anything not already decided.
    change.setdefault("needs_llm", _default_needs_llm(change))
    change.setdefault("confidence", "high" if not change["needs_llm"] else "medium")
    change.setdefault("suggested_action", _default_action(change))

    if change["jinja_location"] is None and change.get("suggested_action") != "skip":
        # We don't know where this belongs in the template.
        change["needs_llm"] = True
        change["confidence"] = "low"

    return change


def _default_needs_llm(change: dict) -> bool:
    # New top-level assignments and structural dict changes need judgment.
    return change["type"] in {"new_assignment", "dict_entry_changed"}


def _default_action(change: dict) -> str:
    mapping = {
        "list_item_added": "append_to_list",
        "list_item_removed": "remove_from_list",
        "value_changed": "update_value",
        "new_assignment": None,
        "removed_assignment": "review_removal",
        "dict_entry_changed": None,
        "import_added": "add_import",
        "import_removed": "review_removal",
    }
    return mapping.get(change["type"])


def build_report(
    old_src: str,
    new_src: str,
    section_map: dict,
    divergences: dict,
    requirements_lines: list,
    copier_data: dict,
    old_version: str,
    new_version: str,
) -> dict:
    old_tree = parse(old_src)
    new_tree = parse(new_src)

    old_assign = top_level_assignments(old_tree)
    new_assign = top_level_assignments(new_tree)

    changes = diff_assignments(old_assign, new_assign)
    changes.extend(diff_imports(old_tree, new_tree))

    resolved = []
    skipped = []
    for change in changes:
        resolve_divergence(change, divergences)
        enrich(change, section_map, requirements_lines, copier_data)
        if change.get("suggested_action") == "skip":
            skipped.append(change)
        else:
            resolved.append(change)

    summary = {
        "old_version": old_version,
        "new_version": new_version,
        "total_changes": len(changes),
        "actionable": len(resolved),
        "skipped": len(skipped),
        "auto_applicable": sum(1 for c in resolved if not c.get("needs_llm")),
        "needs_llm_judgment": sum(1 for c in resolved if c.get("needs_llm")),
    }

    return {
        "summary": summary,
        "changes": resolved,
        "skipped_changes": skipped,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-upstream", required=True)
    parser.add_argument("--new-upstream", required=True)
    parser.add_argument("--section-map", required=True)
    parser.add_argument("--divergences", required=True)
    parser.add_argument("--requirements", default=None)
    parser.add_argument("--copier", default=None)
    parser.add_argument("--old-version", default="unknown")
    parser.add_argument("--new-version", default="unknown")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    old_src = load_source(args.old_upstream)
    new_src = load_source(args.new_upstream)

    section_map = json.loads(Path(args.section_map).read_text())["sections"]
    divergences = json.loads(Path(args.divergences).read_text())["divergences"]

    requirements_lines = []
    if args.requirements and Path(args.requirements).exists():
        requirements_lines = Path(args.requirements).read_text().splitlines()

    copier_data = {}
    if args.copier and Path(args.copier).exists():
        copier_data = _load_copier(Path(args.copier).read_text())

    report = build_report(
        old_src,
        new_src,
        section_map,
        divergences,
        requirements_lines,
        copier_data,
        args.old_version,
        args.new_version,
    )

    output = json.dumps(report, indent=2)
    if args.output == "-":
        print(output)
    else:
        Path(args.output).write_text(output + "\n")
        print(f"Wrote analysis to {args.output}", file=sys.stderr)


def _load_copier(text: str) -> dict:
    """Load copier.yml, tolerating a missing PyYAML by returning {}."""
    try:
        import yaml
    except ImportError:
        print(
            "WARNING: PyYAML not installed; skipping copier.yml default checks.",
            file=sys.stderr,
        )
        return {}
    data = yaml.safe_load(text) or {}
    return {k: v for k, v in data.items() if not k.startswith("_")}


if __name__ == "__main__":
    main()
