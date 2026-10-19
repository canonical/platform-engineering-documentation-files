#!/usr/bin/env python3
"""Sync template files from a ``canonical/sphinx-stack`` release snapshot.

Instead of downloading a hardcoded list of files, this script downloads the
complete upstream release snapshot and classifies every file in it with the
declarative ownership policy in ``scripts/sphinx_stack_sync_policy.json``:

* ``mirror``   -- upstream owns the file; copy it verbatim and track it.
* ``merge``    -- combine upstream changes with local content (``handler``).
* ``preserve`` -- the local copy is owned by this repository; never touch it.
* ``report``   -- list the file for manual review when it changes upstream.
* ``ignore``   -- upstream-only content that is not part of the template.

Mirrored files are tracked in ``scripts/sphinx_stack_sync_state.json`` with the
hash of the content last synced. That makes it possible to:

* update a mirrored file only if it was not modified locally since the last
  sync (local modifications are reported as conflicts, never overwritten);
* delete a mirrored file that was removed upstream, but only if the local
  copy still matches what was last synced.

When no state file exists yet, the state is bootstrapped from the snapshot of
the previously synced release (``--baseline-ref``), so that files which were
synced by earlier versions of the workflow are recognized as upstream-owned.

The script writes a machine-readable JSON report and a Markdown summary that
the workflow uses as the pull request body.

Usage:
    python3 scripts/sync_sphinx_stack.py \\
        --ref 3.0 \\
        --baseline-ref 2.0 \\
        --report-json "$RUNNER_TEMP/sync-report.json" \\
        --report-md "$RUNNER_TEMP/sync-report.md"

Pass ``--upstream-dir`` / ``--baseline-dir`` to use already-extracted
snapshots instead of downloading them.
"""

import argparse
import functools
import hashlib
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

ACTIONS = ("mirror", "merge", "preserve", "report", "ignore")
STATE_VERSION = 1
DEFAULT_POLICY = "scripts/sphinx_stack_sync_policy.json"
DEFAULT_STATE = "scripts/sphinx_stack_sync_state.json"
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
# Statuses that require a human to look at the sync pull request.
ATTENTION_STATUSES = ("conflict", "review", "orphaned", "untracked")
# Keeps the Markdown report well under GitHub's 65,536-character PR body limit.
MAX_MARKDOWN_LENGTH = 60000


class SyncError(Exception):
    """Raised for invalid input such as a malformed policy or snapshot."""


# ── Policy ─────────────────────────────────────────────────────


@functools.cache
def compile_pattern(pattern: str) -> re.Pattern:
    """Compile a glob pattern where ``*`` stays within a segment and ``**`` spans segments."""
    regex = ""
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            regex += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            regex += ".*"
            i += 2
        elif pattern[i] == "*":
            regex += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            regex += "[^/]"
            i += 1
        else:
            regex += re.escape(pattern[i])
            i += 1
    return re.compile(regex + r"\Z")


@dataclass(frozen=True)
class Rule:
    match: str
    action: str
    handler: str | None = None
    reason: str | None = None

    def matches(self, path: str) -> bool:
        return compile_pattern(self.match).match(path) is not None


@dataclass(frozen=True)
class Policy:
    upstream: str
    destination: str
    unmatched: str
    rules: tuple[Rule, ...]

    def classify(self, path: str) -> tuple[str, Rule | None]:
        """Return the action for an upstream-relative path and the rule that matched."""
        for rule in self.rules:
            if rule.matches(path):
                return rule.action, rule
        return self.unmatched, None


def load_policy(path: Path) -> Policy:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1:
        raise SyncError(f"{path}: unsupported policy version {data.get('version')!r}")
    upstream = data.get("upstream", "")
    if not _REPOSITORY_RE.match(upstream):
        raise SyncError(f"{path}: 'upstream' must be an 'owner/repo' name, got {upstream!r}")
    destination = data.get("destination", "")
    dest = PurePosixPath(destination)
    if not destination or dest.is_absolute() or ".." in dest.parts:
        raise SyncError(f"{path}: 'destination' must be a relative path inside the repository")
    unmatched = data.get("unmatched", "report")
    if unmatched not in ("report", "ignore"):
        raise SyncError(f"{path}: 'unmatched' must be 'report' or 'ignore'")
    rules = []
    for index, raw in enumerate(data.get("rules", [])):
        action = raw.get("action")
        if not raw.get("match") or action not in ACTIONS:
            raise SyncError(f"{path}: rule {index} needs 'match' and one of {ACTIONS}")
        handler = raw.get("handler")
        if action == "merge" and handler not in MERGE_HANDLERS:
            raise SyncError(
                f"{path}: rule {index} needs a 'handler' from {sorted(MERGE_HANDLERS)}"
            )
        rules.append(Rule(raw["match"], action, handler, raw.get("reason")))
    return Policy(upstream, destination, unmatched, tuple(rules))


# ── Files and snapshots ────────────────────────────────────────


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def list_files(root: Path) -> dict[str, str]:
    """Map every regular file under ``root`` (relative POSIX path) to its hash."""
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        for name in filenames:
            path = Path(dirpath) / name
            if path.is_file() and not path.is_symlink():
                files[path.relative_to(root).as_posix()] = file_hash(path)
    return files


def extract_snapshot(archive: Path, target: Path) -> Path:
    """Safely extract a GitHub source tarball and return its single top-level directory."""
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tar:
        if hasattr(tarfile, "data_filter"):
            tar.extractall(target, filter="data")
        else:  # pragma: no cover - Python without extraction filters
            root = target.resolve()
            members = []
            for member in tar.getmembers():
                dest = (target / member.name).resolve()
                if not (member.isfile() or member.isdir()) or root not in dest.parents:
                    continue
                members.append(member)
            tar.extractall(target, members=members)  # noqa: S202
    entries = [p for p in target.iterdir() if p.is_dir()]
    if len(entries) != 1:
        raise SyncError(f"{archive}: expected one top-level directory in the snapshot")
    return entries[0]


def download_snapshot(repository: str, ref: str, workdir: Path) -> Path:
    """Download and extract the source snapshot of ``repository`` at tag ``ref``."""
    if not _REPOSITORY_RE.match(repository):
        raise SyncError(f"invalid repository name {repository!r}")
    quoted = urllib.parse.quote(ref, safe="")
    url = f"https://github.com/{repository}/archive/refs/tags/{quoted}.tar.gz"
    workdir.mkdir(parents=True, exist_ok=True)
    archive = workdir / "snapshot.tar.gz"
    print(f"Downloading {url}", file=sys.stderr)
    try:
        with urllib.request.urlopen(url, timeout=60) as resp, archive.open("wb") as out:  # noqa: S310
            shutil.copyfileobj(resp, out)
    except urllib.error.URLError as exc:
        raise SyncError(f"failed to download {url}: {exc}") from exc
    return extract_snapshot(archive, workdir / "source")


def copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    shutil.copymode(src, dest)


def prune_empty_dirs(start: Path, stop: Path) -> None:
    """Remove empty directories from ``start`` up to, but excluding, ``stop``."""
    current = start
    while current != stop and stop in current.parents and not any(current.iterdir()):
        current.rmdir()
        current = current.parent


# ── State ──────────────────────────────────────────────────────


def load_state(path: Path) -> dict | None:
    if not path.is_file():
        return None
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("version") != STATE_VERSION:
        raise SyncError(f"{path}: unsupported state version {state.get('version')!r}")
    return state


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# ── Merge handlers ─────────────────────────────────────────────

_REQUIREMENT_NAME = re.compile(r"^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)")


def parse_requirements(text: str) -> dict[str, tuple[str, str]]:
    """Map normalized package names (or option lines) to ``(requirement, raw line)``.

    The requirement has inline comments stripped and is used for comparison;
    the raw line keeps upstream comments and is used when appending.
    """
    requirements = {}
    for raw in text.splitlines():
        line = re.sub(r"(^|\s)#.*$", "", raw).strip()
        if not line:
            continue
        match = _REQUIREMENT_NAME.match(line)
        if match and not line.startswith("-"):
            key = re.sub(r"[-_.]+", "-", match.group(1)).lower()
        else:
            key = line
        requirements.setdefault(key, (line, raw.strip()))
    return requirements


def merge_requirements(local: Path, upstream: Path, ref: str, dry_run: bool) -> dict:
    """Append upstream dependencies whose package is not listed locally.

    Version specifiers of packages already listed locally are left alone
    (they are managed locally, for example by Renovate) but are reported.
    """
    upstream_text = upstream.read_text(encoding="utf-8")
    if not local.is_file():
        if not dry_run:
            copy_file(upstream, local)
        added = [raw for _, raw in parse_requirements(upstream_text).values()]
        return {"status": "added", "added": added, "version_differences": [], "local_only": []}

    local_text = local.read_text(encoding="utf-8")
    local_reqs = parse_requirements(local_text)
    upstream_reqs = parse_requirements(upstream_text)
    added = [raw for key, (_, raw) in upstream_reqs.items() if key not in local_reqs]
    differences = [
        {"name": key, "local": local_reqs[key][0], "upstream": line}
        for key, (line, _) in upstream_reqs.items()
        if key in local_reqs and local_reqs[key][0] != line
    ]
    local_only = [line for key, (line, _) in local_reqs.items() if key not in upstream_reqs]

    if added and not dry_run:
        if not local_text:
            separator = ""
        elif local_text.endswith("\n"):
            separator = "\n"
        else:
            separator = "\n\n"
        block = f"{separator}# Added from sphinx-stack {ref}\n" + "".join(
            f"{line}\n" for line in added
        )
        local.write_text(local_text + block, encoding="utf-8")
    return {
        "status": "merged" if added else "unchanged",
        "added": added,
        "version_differences": differences,
        "local_only": local_only,
    }


MERGE_HANDLERS = {"requirements": merge_requirements}


# ── Sync ───────────────────────────────────────────────────────


def _mirror(src: Path, local: Path, upstream_hash: str, recorded: str | None, dry_run: bool):
    """Return ``(status, detail, hash to track or None)`` for one mirrored file."""
    if local.exists() and not local.is_file():
        return "conflict", "Local path exists but is not a regular file.", recorded
    local_hash = file_hash(local) if local.is_file() else None
    if local_hash == upstream_hash:
        return "unchanged", None, upstream_hash
    if local_hash is None:
        if recorded is None:
            if not dry_run:
                copy_file(src, local)
            return "added", "New upstream file.", upstream_hash
        return "conflict", "Previously synced file was deleted locally; not restored.", recorded
    if recorded is not None and local_hash == recorded:
        if not dry_run:
            copy_file(src, local)
        return "updated", None, upstream_hash
    if recorded is None:
        detail = "Local file is not tracked and differs from upstream; left unchanged."
    else:
        detail = "Local file was modified since the last sync; left unchanged."
    return "conflict", detail, recorded


def sync(
    policy: Policy,
    repo_root: Path,
    upstream_dir: Path,
    ref: str,
    state: dict | None,
    baseline_dir: Path | None = None,
    baseline_ref: str | None = None,
    dry_run: bool = False,
) -> tuple[dict, dict]:
    """Apply ``policy`` to the snapshot in ``upstream_dir``. Return ``(new_state, report)``."""
    dest_root = repo_root / policy.destination
    upstream_files = list_files(upstream_dir)
    if not upstream_files:
        raise SyncError(f"{upstream_dir}: upstream snapshot contains no files")

    bootstrap = None
    if state is None:
        if baseline_dir is not None:
            previous_upstream = list_files(baseline_dir)
            tracked = {
                path: digest
                for path, digest in previous_upstream.items()
                if policy.classify(path)[0] == "mirror" and (dest_root / path).is_file()
            }
            bootstrap = {"mode": "baseline", "ref": baseline_ref, "tracked": sorted(tracked)}
        else:
            previous_upstream, tracked = None, {}
            bootstrap = {"mode": "empty", "ref": None, "tracked": []}
        previous_ref = baseline_ref
    else:
        previous_upstream = state.get("upstream_files")
        tracked = dict(state.get("mirrored", {}))
        previous_ref = state.get("ref")

    entries = []
    mirrored = {}

    def add_entry(path, action, rule, status, detail=None, **extra):
        entry = {
            "path": path,
            "local_path": (PurePosixPath(policy.destination) / path).as_posix(),
            "action": action,
            "rule": rule.match if rule else None,
            "reason": rule.reason if rule else None,
            "status": status,
            "detail": detail,
        }
        entry.update(extra)
        entries.append(entry)
        return entry

    for path, upstream_hash in sorted(upstream_files.items()):
        action, rule = policy.classify(path)
        src, local = upstream_dir / path, dest_root / path
        if action == "mirror":
            status, detail, keep = _mirror(src, local, upstream_hash, tracked.get(path), dry_run)
            if keep is not None:
                mirrored[path] = keep
            add_entry(path, action, rule, status, detail)
            continue
        if action == "merge":
            if local.exists() and not local.is_file():
                detail = "Local path exists but is not a regular file."
                entry = add_entry(path, action, rule, "conflict", detail)
            else:
                result = MERGE_HANDLERS[rule.handler](local, src, ref, dry_run)
                entry = add_entry(path, action, rule, result.pop("status"), None, merge=result)
        elif action == "preserve":
            entry = add_entry(path, action, rule, "preserved")
        elif action == "ignore":
            entry = add_entry(path, action, rule, "ignored")
        else:  # report, including unmatched files
            if previous_upstream is None:
                status, detail = "review", "No previous snapshot to compare against."
            elif path not in previous_upstream:
                status, detail = "review", "New upstream file."
            elif previous_upstream[path] != upstream_hash:
                status, detail = "review", "Changed upstream."
            else:
                status, detail = "unchanged", None
            if rule is None and status == "review":
                detail += " Not covered by the sync policy."
            entry = add_entry(path, action, rule, status, detail)
        if path in tracked:
            if entry["status"] not in ATTENTION_STATUSES:
                entry["status"] = "untracked"
            entry["detail"] = " ".join(
                filter(None, [entry["detail"], "Stopped tracking: no longer mirrored by policy."])
            )

    # Previously mirrored files that no longer exist upstream.
    for path, recorded in sorted(tracked.items()):
        if path in upstream_files:
            continue
        action, rule = policy.classify(path)
        local = dest_root / path
        if not local.is_file():
            add_entry(path, action, rule, "removed", "Removed upstream; already absent locally.")
        elif action != "mirror":
            detail = "Removed upstream, but no longer mirrored by policy; left in place."
            add_entry(path, action, rule, "untracked", detail)
        elif file_hash(local) == recorded:
            if not dry_run:
                local.unlink()
                prune_empty_dirs(local.parent, dest_root)
            add_entry(path, action, rule, "removed", "Removed upstream.")
        else:
            mirrored[path] = recorded
            detail = "Removed upstream, but modified locally; left in place."
            add_entry(path, action, rule, "conflict", detail)

    # Local files covered by a mirror rule that are neither upstream nor tracked.
    if dest_root.is_dir():
        for path in sorted(list_files(dest_root)):
            if path in upstream_files or path in tracked:
                continue
            action, rule = policy.classify(path)
            if action == "mirror":
                detail = "Matches a mirror rule but is absent upstream and untracked; kept."
                add_entry(path, action, rule, "orphaned", detail)

    upstream_changes = None
    if previous_upstream is not None:
        upstream_changes = {
            "added": sorted(set(upstream_files) - set(previous_upstream)),
            "removed": sorted(set(previous_upstream) - set(upstream_files)),
            "modified": sorted(
                p
                for p in set(upstream_files) & set(previous_upstream)
                if upstream_files[p] != previous_upstream[p]
            ),
        }

    summary = {}
    for entry in entries:
        summary[entry["status"]] = summary.get(entry["status"], 0) + 1

    new_state = {
        "version": STATE_VERSION,
        "upstream": policy.upstream,
        "ref": ref,
        "mirrored": dict(sorted(mirrored.items())),
        "upstream_files": dict(sorted(upstream_files.items())),
    }
    report = {
        "upstream": policy.upstream,
        "ref": ref,
        "previous_ref": previous_ref,
        "dry_run": dry_run,
        "bootstrap": bootstrap,
        "summary": dict(sorted(summary.items())),
        "upstream_changes": upstream_changes,
        "files": entries,
    }
    return new_state, report


# ── Reporting ──────────────────────────────────────────────────


def _cell(text) -> str:
    return str(text or "").replace("|", "\\|").replace("\n", " ")


def _code(text) -> str:
    return f"`{text}`"


def render_markdown(report: dict, policy_path: str = DEFAULT_POLICY, compact: bool = False) -> str:
    """Render the report as Markdown. ``compact`` omits the informational file lists."""
    upstream, ref = report["upstream"], report["ref"]
    previous = report.get("previous_ref")
    title = f"{_code(previous)} → {_code(ref)}" if previous else _code(ref)
    lines = [
        f"## Sphinx Stack sync: {title}",
        "",
        f"Automated sync from [{upstream}](https://github.com/{upstream}/releases/tag/"
        f"{urllib.parse.quote(ref, safe='')}), classified by {_code(policy_path)}.",
        "",
    ]
    bootstrap = report.get("bootstrap")
    if bootstrap and bootstrap["mode"] == "baseline":
        lines += [
            f"> ℹ️ No sync state existed. It was bootstrapped from upstream "
            f"{_code(bootstrap['ref'])}: {len(bootstrap['tracked'])} local file(s) were "
            "recognized as previously mirrored.",
            "",
        ]
    elif bootstrap:
        lines += [
            "> ℹ️ No sync state or previous release was available. Only local files identical "
            "to upstream are tracked; differing files are reported as conflicts.",
            "",
        ]

    files = report["files"]
    changed = [e for e in files if e["action"] == "mirror" and e["status"] in ("added", "updated")]
    changed += [e for e in files if e["status"] == "removed"]
    lines += ["### Mirrored from upstream", ""]
    if changed:
        lines += ["| File | Change |", "| --- | --- |"]
        lines += [f"| {_code(e['local_path'])} | {e['status']} |" for e in changed]
    else:
        lines.append("_No mirrored files changed._")
    lines.append("")

    merged = [e for e in files if e["action"] == "merge"]
    if merged:
        lines += ["### Merged", ""]
        for entry in merged:
            merge = entry["merge"]
            if merge["added"]:
                added = ", ".join(_code(line) for line in merge["added"])
                lines.append(f"- {_code(entry['local_path'])}: added {added}")
            else:
                lines.append(f"- {_code(entry['local_path'])}: no new dependencies")
            if merge["version_differences"]:
                lines += [
                    "",
                    "<details><summary>"
                    f"{len(merge['version_differences'])} version difference(s), left unchanged"
                    "</summary>",
                    "",
                    "| Package | Local | Upstream |",
                    "| --- | --- | --- |",
                ]
                lines += [
                    f"| {_cell(d['name'])} | {_code(_cell(d['local']))} "
                    f"| {_code(_cell(d['upstream']))} |"
                    for d in merge["version_differences"]
                ]
                lines += ["", "</details>"]
            if merge["local_only"]:
                lines += [
                    "",
                    "<details><summary>"
                    f"{len(merge['local_only'])} local requirement(s) not listed upstream"
                    "</summary>",
                    "",
                ]
                lines += [f"- {_code(line)}" for line in merge["local_only"]]
                lines += ["", "</details>"]
        lines += [
            "",
            "> ⚠️ If new Sphinx extensions were added to `requirements.txt`, verify whether "
            "`conf.py.jinja`'s `extensions` list needs updating.",
            "",
        ]

    attention = [e for e in files if e["status"] in ATTENTION_STATUSES]
    lines += ["### ⚠️ Needs attention", ""]
    if attention:
        lines += ["| File | Action | Status | Details |", "| --- | --- | --- | --- |"]
        for e in attention:
            detail = " ".join(filter(None, [e["detail"], e["reason"]]))
            lines.append(
                f"| {_code(e['path'])} | {e['action'] if e['rule'] else 'unmatched'} "
                f"| {e['status']} | {_cell(detail)} |"
            )
    else:
        lines.append("_Nothing to review._")
    lines.append("")

    changes = report.get("upstream_changes")
    if compact:
        lines += ["_Unchanged files and upstream change lists omitted; see the JSON report._", ""]
    elif changes and any(changes.values()):
        lines += [
            f"<details><summary>All upstream file changes since {_code(previous)}</summary>",
            "",
        ]
        for kind in ("added", "modified", "removed"):
            lines += [f"- {kind}: {_code(p)}" for p in changes[kind]]
        lines += ["", "</details>", ""]

    quiet = [e for e in files if e["status"] in ("unchanged", "preserved", "ignored")]
    if quiet and not compact:
        lines += [
            f"<details><summary>{len(quiet)} unchanged, preserved, or ignored file(s)</summary>",
            "",
        ]
        lines += [f"- {_code(e['path'])}: {e['status']}" for e in quiet]
        lines += ["", "</details>", ""]
    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--ref", required=True, help="Upstream release tag to sync to.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--policy", default=DEFAULT_POLICY, help="Relative to --repo-root.")
    parser.add_argument("--state", default=DEFAULT_STATE, help="Relative to --repo-root.")
    parser.add_argument("--upstream-dir", type=Path, help="Use an extracted snapshot.")
    parser.add_argument(
        "--baseline-ref",
        help="Previously synced release; used to bootstrap a missing state file.",
    )
    parser.add_argument("--baseline-dir", type=Path, help="Use an extracted baseline snapshot.")
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--report-md", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Report without writing files.")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    policy = load_policy(repo_root / args.policy)
    state_path = repo_root / args.state
    state = load_state(state_path)

    with tempfile.TemporaryDirectory(prefix="sphinx-stack-") as tmp:
        upstream_dir = args.upstream_dir or download_snapshot(
            policy.upstream, args.ref, Path(tmp) / "upstream"
        )
        baseline_dir = None
        if state is None:
            baseline_dir = args.baseline_dir
            if baseline_dir is None and args.baseline_ref:
                baseline_dir = download_snapshot(
                    policy.upstream, args.baseline_ref, Path(tmp) / "baseline"
                )
        new_state, report = sync(
            policy,
            repo_root,
            upstream_dir,
            args.ref,
            state,
            baseline_dir=baseline_dir,
            baseline_ref=args.baseline_ref,
            dry_run=args.dry_run,
        )

    if not args.dry_run:
        write_json(state_path, new_state)
    markdown = render_markdown(report, args.policy)
    if len(markdown) > MAX_MARKDOWN_LENGTH:
        markdown = render_markdown(report, args.policy, compact=True)
    if len(markdown) > MAX_MARKDOWN_LENGTH:
        note = "\n\n_Report truncated; see the JSON report for all entries._\n"
        markdown = markdown[: MAX_MARKDOWN_LENGTH - len(note)] + note
    if args.report_json:
        write_json(args.report_json, report)
    if args.report_md:
        args.report_md.parent.mkdir(parents=True, exist_ok=True)
        args.report_md.write_text(markdown, encoding="utf-8")
    print(markdown)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
