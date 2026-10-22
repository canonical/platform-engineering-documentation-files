"""Unit tests for scripts/sync_sphinx_stack.py.

Run with: python3 -m unittest discover -s tests -v
"""

import contextlib
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import sync_sphinx_stack as sss  # noqa: E402

POLICY = {
    "version": 1,
    "upstream": "canonical/sphinx-stack",
    "destination": "template",
    "unmatched": "report",
    "rules": [
        {"match": "docs/requirements.txt", "action": "merge", "handler": "requirements"},
        {"match": "docs/conf.py", "action": "report", "reason": "Adapt manually."},
        {"match": "docs/_dev/**", "action": "mirror"},
        {"match": "docs/_templates/**", "action": "mirror"},
        {"match": "docs/Makefile", "action": "mirror"},
        {"match": "docs/redirects.txt", "action": "preserve"},
        {"match": "docs/**/*.rst", "action": "ignore"},
    ],
}


def write_tree(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def h(content: str) -> str:
    return sss.hashlib.sha256(content.encode()).hexdigest()


class SyncTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        policy_path = self.tmp / "policy.json"
        policy_path.write_text(json.dumps(POLICY), encoding="utf-8")
        self.policy = sss.load_policy(policy_path)

    def tearDown(self):
        self._tmp.cleanup()

    def snapshot(self, name: str, files: dict[str, str]) -> Path:
        root = self.tmp / name
        write_tree(root, files)
        return root

    def local(self, rel: str) -> Path:
        return self.repo / "template" / rel

    def run_sync(self, upstream, state, ref="2.0", **kwargs):
        return sss.sync(self.policy, self.repo, upstream, ref, state, **kwargs)

    @staticmethod
    def entry(report, path):
        matches = [e for e in report["files"] if e["path"] == path]
        assert len(matches) == 1, (path, matches)
        return matches[0]


class PolicyTests(SyncTestCase):
    def test_glob_semantics(self):
        self.assertTrue(sss.compile_pattern("docs/_dev/**").match("docs/_dev/a/b.py"))
        self.assertTrue(sss.compile_pattern("docs/**/*.rst").match("docs/index.rst"))
        self.assertTrue(sss.compile_pattern("docs/**/*.rst").match("docs/a/b/c.rst"))
        self.assertFalse(sss.compile_pattern("docs/*.rst").match("docs/a/b.rst"))
        self.assertFalse(sss.compile_pattern("docs/Makefile").match("docs/Makefile.bak"))

    def test_first_matching_rule_wins_and_unmatched_default(self):
        self.assertEqual(self.policy.classify("docs/_dev/x.py")[0], "mirror")
        self.assertEqual(self.policy.classify("docs/how-to/index.rst")[0], "ignore")
        action, rule = self.policy.classify("brand/new/file.txt")
        self.assertEqual((action, rule), ("report", None))

    def test_invalid_policy_is_rejected(self):
        bad = dict(POLICY, rules=[{"match": "x", "action": "merge", "handler": "nope"}])
        path = self.tmp / "bad.json"
        path.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(sss.SyncError):
            sss.load_policy(path)
        path.write_text(json.dumps(dict(POLICY, destination="../outside")), encoding="utf-8")
        with self.assertRaises(sss.SyncError):
            sss.load_policy(path)


class MirrorTests(SyncTestCase):
    def test_mirrors_new_and_updated_tracked_files(self):
        write_tree(self.repo / "template", {"docs/_dev/tool.py": "v1\n"})
        state = {"version": 1, "mirrored": {"docs/_dev/tool.py": h("v1\n")}}
        upstream = self.snapshot(
            "up",
            {"docs/_dev/tool.py": "v2\n", "docs/_dev/nested/new.json": "{}\n"},
        )

        new_state, report = self.run_sync(upstream, state)

        self.assertEqual(self.local("docs/_dev/tool.py").read_text(), "v2\n")
        self.assertEqual(self.local("docs/_dev/nested/new.json").read_text(), "{}\n")
        self.assertEqual(self.entry(report, "docs/_dev/tool.py")["status"], "updated")
        self.assertEqual(self.entry(report, "docs/_dev/nested/new.json")["status"], "added")
        self.assertEqual(
            new_state["mirrored"],
            {"docs/_dev/tool.py": h("v2\n"), "docs/_dev/nested/new.json": h("{}\n")},
        )

    def test_preserves_executable_bit(self):
        upstream = self.snapshot("up", {"docs/_dev/run.py": "#!/bin/sh\n"})
        (upstream / "docs/_dev/run.py").chmod(0o755)
        self.run_sync(upstream, {"version": 1, "mirrored": {}})
        self.assertTrue(self.local("docs/_dev/run.py").stat().st_mode & 0o100)

    def test_locally_modified_file_is_not_overwritten(self):
        write_tree(self.repo / "template", {"docs/Makefile": "local fix\n"})
        state = {"version": 1, "mirrored": {"docs/Makefile": h("v1\n")}}
        upstream = self.snapshot("up", {"docs/Makefile": "v2\n"})

        new_state, report = self.run_sync(upstream, state)

        self.assertEqual(self.local("docs/Makefile").read_text(), "local fix\n")
        self.assertEqual(self.entry(report, "docs/Makefile")["status"], "conflict")
        # The last synced hash is kept so the conflict is reported until resolved.
        self.assertEqual(new_state["mirrored"]["docs/Makefile"], h("v1\n"))

    def test_missing_upstream_directory_does_not_fail(self):
        # Upstream dropped docs/_templates/ entirely; nothing was tracked there.
        write_tree(self.repo / "template", {"docs/_dev/tool.py": "v1\n"})
        upstream = self.snapshot("up", {"docs/_dev/tool.py": "v1\n"})

        new_state, report = self.run_sync(upstream, {"version": 1, "mirrored": {}})

        self.assertEqual(report["summary"], {"unchanged": 1})
        self.assertEqual(new_state["mirrored"], {"docs/_dev/tool.py": h("v1\n")})

    def test_dry_run_does_not_write(self):
        upstream = self.snapshot("up", {"docs/_dev/tool.py": "v1\n"})
        _, report = self.run_sync(upstream, {"version": 1, "mirrored": {}}, dry_run=True)
        self.assertEqual(self.entry(report, "docs/_dev/tool.py")["status"], "added")
        self.assertFalse(self.local("docs/_dev/tool.py").exists())


class RemovalTests(SyncTestCase):
    def test_unmodified_file_removed_upstream_is_deleted(self):
        write_tree(
            self.repo / "template",
            {"docs/_templates/header.html": "<h/>", "docs/_dev/tool.py": "v1\n"},
        )
        state = {
            "version": 1,
            "mirrored": {"docs/_templates/header.html": h("<h/>"), "docs/_dev/tool.py": h("v1\n")},
        }
        upstream = self.snapshot("up", {"docs/_dev/tool.py": "v1\n"})

        new_state, report = self.run_sync(upstream, state)

        self.assertFalse(self.local("docs/_templates/header.html").exists())
        self.assertFalse(self.local("docs/_templates").exists(), "empty dir should be pruned")
        self.assertEqual(self.entry(report, "docs/_templates/header.html")["status"], "removed")
        self.assertNotIn("docs/_templates/header.html", new_state["mirrored"])

    def test_modified_file_removed_upstream_is_kept_and_reported(self):
        write_tree(self.repo / "template", {"docs/_templates/header.html": "<custom/>"})
        state = {"version": 1, "mirrored": {"docs/_templates/header.html": h("<h/>")}}
        upstream = self.snapshot("up", {"docs/_dev/tool.py": "v1\n"})

        new_state, report = self.run_sync(upstream, state)

        self.assertEqual(self.local("docs/_templates/header.html").read_text(), "<custom/>")
        self.assertEqual(self.entry(report, "docs/_templates/header.html")["status"], "conflict")
        self.assertIn("docs/_templates/header.html", new_state["mirrored"])

    def test_untracked_local_file_under_mirror_rule_is_reported_not_deleted(self):
        write_tree(self.repo / "template", {"docs/_dev/local_only.py": "x\n"})
        upstream = self.snapshot("up", {"docs/_dev/tool.py": "v1\n"})

        _, report = self.run_sync(upstream, {"version": 1, "mirrored": {}})

        self.assertTrue(self.local("docs/_dev/local_only.py").exists())
        self.assertEqual(self.entry(report, "docs/_dev/local_only.py")["status"], "orphaned")


class RequirementsMergeTests(SyncTestCase):
    def test_appends_only_new_packages(self):
        write_tree(
            self.repo / "template",
            {
                "docs/requirements.txt": "# Theme\ncanonical-sphinx==0.7.1\n"
                "myst_parser==4.0.1  # pinned\nvale==3.22.0.0"
            },
        )
        upstream = self.snapshot(
            "up",
            {
                "docs/requirements.txt": "ulwazi~=1.0\nMyst-Parser~=4.0\n"
                "vale==3.13.0.0\nsphinx-modern-pdf-style~=0.1\n"
            },
        )

        _, report = self.run_sync(upstream, {"version": 1, "mirrored": {}}, ref="3.0")

        text = self.local("docs/requirements.txt").read_text()
        self.assertEqual(
            text,
            "# Theme\ncanonical-sphinx==0.7.1\nmyst_parser==4.0.1  # pinned\nvale==3.22.0.0\n"
            "\n# Added from sphinx-stack 3.0\nulwazi~=1.0\nsphinx-modern-pdf-style~=0.1\n",
        )
        entry = self.entry(report, "docs/requirements.txt")
        self.assertEqual(entry["status"], "merged")
        self.assertEqual(entry["merge"]["added"], ["ulwazi~=1.0", "sphinx-modern-pdf-style~=0.1"])
        self.assertEqual(
            [d["name"] for d in entry["merge"]["version_differences"]], ["myst-parser", "vale"]
        )
        self.assertEqual(entry["merge"]["local_only"], ["canonical-sphinx==0.7.1"])

    def test_appended_lines_keep_upstream_comments(self):
        write_tree(self.repo / "template", {"docs/requirements.txt": "sphinx==8.0\n"})
        upstream = self.snapshot("up", {"docs/requirements.txt": "newpkg~=1.0  # needed for X\n"})

        self.run_sync(upstream, {"version": 1, "mirrored": {}}, ref="3.0")

        self.assertTrue(
            self.local("docs/requirements.txt")
            .read_text()
            .endswith("# Added from sphinx-stack 3.0\nnewpkg~=1.0  # needed for X\n")
        )

    def test_empty_local_requirements_has_no_leading_blank_line(self):
        write_tree(self.repo / "template", {"docs/requirements.txt": ""})
        upstream = self.snapshot("up", {"docs/requirements.txt": "pkg\n"})

        self.run_sync(upstream, {"version": 1, "mirrored": {}}, ref="3.0")

        self.assertEqual(
            self.local("docs/requirements.txt").read_text(), "# Added from sphinx-stack 3.0\npkg\n"
        )

    def test_no_new_packages_leaves_file_untouched(self):
        content = "sphinx==8.0\n"
        write_tree(self.repo / "template", {"docs/requirements.txt": content})
        upstream = self.snapshot("up", {"docs/requirements.txt": "Sphinx~=8.0\n"})

        _, report = self.run_sync(upstream, {"version": 1, "mirrored": {}})

        self.assertEqual(self.local("docs/requirements.txt").read_text(), content)
        self.assertEqual(self.entry(report, "docs/requirements.txt")["status"], "unchanged")


class BootstrapTests(SyncTestCase):
    def test_bootstraps_state_from_baseline_release(self):
        write_tree(
            self.repo / "template",
            {
                "docs/_templates/header.html": "<h/>",  # identical to baseline
                "docs/Makefile": "local fix\n",  # modified after the baseline sync
                "docs/_dev/tool.py": "v2\n",  # already equal to the new release
            },
        )
        baseline = self.snapshot(
            "base",
            {
                "docs/_templates/header.html": "<h/>",
                "docs/Makefile": "v1\n",
                "docs/_dev/tool.py": "v1\n",
                "docs/conf.py": "a = 1\n",
            },
        )
        upstream = self.snapshot(
            "up",
            {"docs/Makefile": "v2\n", "docs/_dev/tool.py": "v2\n", "docs/conf.py": "a = 2\n"},
        )

        new_state, report = self.run_sync(
            upstream, None, ref="3.0", baseline_dir=baseline, baseline_ref="2.0"
        )

        self.assertEqual(report["bootstrap"]["mode"], "baseline")
        self.assertEqual(report["previous_ref"], "2.0")
        self.assertEqual(
            report["bootstrap"]["tracked"],
            ["docs/Makefile", "docs/_dev/tool.py", "docs/_templates/header.html"],
        )
        self.assertFalse(self.local("docs/_templates/header.html").exists())
        self.assertEqual(self.entry(report, "docs/_templates/header.html")["status"], "removed")
        self.assertEqual(self.entry(report, "docs/Makefile")["status"], "conflict")
        self.assertEqual(self.local("docs/Makefile").read_text(), "local fix\n")
        self.assertEqual(self.entry(report, "docs/_dev/tool.py")["status"], "unchanged")
        conf = self.entry(report, "docs/conf.py")
        self.assertEqual((conf["status"], conf["detail"]), ("review", "Changed upstream."))
        self.assertEqual(report["upstream_changes"]["removed"], ["docs/_templates/header.html"])
        self.assertEqual(new_state["ref"], "3.0")
        self.assertEqual(new_state["upstream_files"]["docs/conf.py"], h("a = 2\n"))

    def test_bootstrap_without_baseline_never_overwrites(self):
        write_tree(self.repo / "template", {"docs/Makefile": "local\n", "docs/_dev/a": "same"})
        upstream = self.snapshot("up", {"docs/Makefile": "v2\n", "docs/_dev/a": "same"})

        new_state, report = self.run_sync(upstream, None)

        self.assertEqual(report["bootstrap"]["mode"], "empty")
        self.assertEqual(self.local("docs/Makefile").read_text(), "local\n")
        self.assertEqual(self.entry(report, "docs/Makefile")["status"], "conflict")
        self.assertEqual(new_state["mirrored"], {"docs/_dev/a": h("same")})

    def test_policy_change_away_from_mirror_is_surfaced(self):
        write_tree(self.repo / "template", {"docs/redirects.txt": "x"})
        upstream = self.snapshot("up", {"docs/redirects.txt": "x"})
        state = {"version": 1, "mirrored": {"docs/redirects.txt": h("x")}}

        new_state, report = self.run_sync(upstream, state)

        entry = self.entry(report, "docs/redirects.txt")
        self.assertEqual(entry["status"], "untracked")
        self.assertIn("Stopped tracking", entry["detail"])
        self.assertEqual(new_state["mirrored"], {})

    def test_report_files_unchanged_upstream_are_quiet(self):
        upstream = self.snapshot("up", {"docs/conf.py": "a = 1\n", "new/thing.txt": "x"})
        state = {
            "version": 1,
            "mirrored": {},
            "upstream_files": {"docs/conf.py": h("a = 1\n")},
        }

        _, report = self.run_sync(upstream, state)

        self.assertEqual(self.entry(report, "docs/conf.py")["status"], "unchanged")
        unmatched = self.entry(report, "new/thing.txt")
        self.assertEqual(unmatched["status"], "review")
        self.assertIn("Not covered by the sync policy", unmatched["detail"])


class CliAndSnapshotTests(SyncTestCase):
    def test_cli_writes_state_and_reports(self):
        (self.repo / "scripts").mkdir()
        (self.repo / "scripts/policy.json").write_text(json.dumps(POLICY), encoding="utf-8")
        write_tree(self.repo / "template", {"docs/_templates/footer.html": "<f/>"})
        baseline = self.snapshot("base", {"docs/_templates/footer.html": "<f/>"})
        upstream = self.snapshot("up", {"docs/_dev/version": "3.0\n"})
        report_json, report_md = self.tmp / "out/report.json", self.tmp / "out/report.md"

        argv = [
            "--repo-root", str(self.repo),
            "--policy", "scripts/policy.json",
            "--state", "scripts/state.json",
            "--ref", "3.0",
            "--upstream-dir", str(upstream),
            "--baseline-ref", "2.0",
            "--baseline-dir", str(baseline),
            "--report-json", str(report_json),
            "--report-md", str(report_md),
        ]  # fmt: skip
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sss.main(argv), 0)

        state = json.loads((self.repo / "scripts/state.json").read_text())
        self.assertEqual(state["ref"], "3.0")
        self.assertEqual(state["mirrored"], {"docs/_dev/version": h("3.0\n")})
        report = json.loads(report_json.read_text())
        self.assertEqual(report["summary"], {"added": 1, "removed": 1})
        markdown = report_md.read_text()
        self.assertIn("`2.0` → `3.0`", markdown)
        self.assertIn("| `template/docs/_templates/footer.html` | removed |", markdown)

    def test_compact_markdown_omits_informational_lists(self):
        upstream = self.snapshot("up", {"docs/_dev/a": "x", "docs/index.rst": "y"})
        _, report = self.run_sync(upstream, {"version": 1, "mirrored": {}})

        full = sss.render_markdown(report)
        compact = sss.render_markdown(report, compact=True)

        self.assertIn("`docs/index.rst`: ignored", full)
        self.assertNotIn("`docs/index.rst`", compact)
        self.assertIn("| `template/docs/_dev/a` | added |", compact)

    def test_extract_snapshot_strips_top_level_directory(self):
        src = self.snapshot("src/sphinx-stack-3.0", {"docs/Makefile": "all:\n"})
        archive = self.tmp / "snap.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(src, arcname="sphinx-stack-3.0")

        root = sss.extract_snapshot(archive, self.tmp / "extracted")

        self.assertEqual(sss.list_files(root), {"docs/Makefile": h("all:\n")})


if __name__ == "__main__":
    unittest.main()
