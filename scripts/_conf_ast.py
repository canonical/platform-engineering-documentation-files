"""Shared AST utilities for parsing Sphinx ``conf.py`` files.

Used by both ``extract_conf_values.py`` (onboarding) and
``analyze_conf_diff.py`` (upstream sync analysis) to statically parse a
Sphinx configuration file without executing it.
"""

import ast


def literal_value(node: ast.expr):
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


def extract_any_value(node: ast.expr):
    """Extract a value from an AST node, handling lists, dicts, and literals.

    Returns a JSON-serializable Python value, or a string placeholder
    for values that cannot be statically resolved.
    """
    # Literals: strings, numbers, booleans, None
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in ("True", "False"):
        return node.id == "True"
    if isinstance(node, ast.Name) and node.id == "None":
        return None

    # Lists: [item, item, ...]
    if isinstance(node, ast.List):
        return [extract_any_value(elt) for elt in node.elts]

    # Tuples: (item, item, ...)
    if isinstance(node, ast.Tuple):
        return [extract_any_value(elt) for elt in node.elts]

    # Dicts: {key: value, ...}
    if isinstance(node, ast.Dict):
        result = {}
        for k, v in zip(node.keys, node.values):
            key = extract_any_value(k)
            val = extract_any_value(v)
            if key is not None:
                result[str(key)] = val
        return result

    # Joined strings (f-strings)
    if isinstance(node, ast.JoinedStr):
        parts = []
        for val in node.values:
            if isinstance(val, ast.Constant):
                parts.append(str(val.value))
            elif isinstance(val, ast.FormattedValue):
                parts.append("{...}")
        return "".join(parts)

    # Function calls, attribute lookups, etc. — return a placeholder
    if isinstance(node, ast.Call):
        func_name = get_name(node.func)
        return f"<call: {func_name}(...)>"

    if isinstance(node, ast.Attribute):
        return f"<attr: {get_name(node)}>"

    # Unary minus
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        if isinstance(node.operand, ast.Constant):
            return -node.operand.value

    return None


def get_name(node: ast.expr) -> str:
    """Get a dotted name string from an AST node (e.g., 'sphinx.util.inspect')."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{get_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return get_name(node.func)
    return "?"


def top_level_assignments(tree: ast.Module) -> dict:
    """Return a mapping of every top-level ``name = value`` assignment.

    Only module-level assignments with a single ``ast.Name`` target are
    included. The value is resolved via :func:`extract_any_value`.
    """
    assignments: dict = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = extract_any_value(node.value)
    return assignments


def imports(tree: ast.Module) -> list:
    """Return a sorted list of imported module names at module level."""
    names: set = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                names.add(f"{module}.{alias.name}" if module else alias.name)
    return sorted(names)
