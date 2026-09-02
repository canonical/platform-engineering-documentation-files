#!/usr/bin/env python3
"""Build a self-contained prompt for the Copilot CLI from the update-conf-py
skill and an analyze_conf_diff.py report.

The prompt inlines the full skill instructions (so the agent doesn't spend
tool calls reading it) followed by the analysis JSON and explicit guardrails.
Output is written to stdout for the workflow to capture into a file.

Usage:
    python3 scripts/build_copilot_prompt.py analysis.json > prompt.txt
    python3 scripts/build_copilot_prompt.py analysis.json --skill path/to/SKILL.md
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_SKILL_PATH = "skills/update-conf-py/SKILL.md"
SUMMARY_OUTPUT_PATH = "/tmp/agent-summary.md"


def build_prompt(skill_text: str, analysis: dict) -> str:
    summary = analysis.get("summary", {})
    changes = analysis.get("changes", [])
    skipped = analysis.get("skipped_changes", [])

    return f"""\
You are maintaining the Copier template at
`template/docs/conf.py.jinja` in the canonical/platform-engineering-documentation-files
repository. A new canonical/sphinx-stack release introduced upstream conf.py
changes. A deterministic script already analyzed the diff; your job is to
apply its findings to the template following the skill instructions below.

=== SKILL INSTRUCTIONS ===
{skill_text}
=== END SKILL INSTRUCTIONS ===

=== ANALYSIS REPORT (sphinx-stack {summary.get("old_version", "?")} \
-> {summary.get("new_version", "?")}) ===
{json.dumps({"summary": summary, "changes": changes}, indent=2)}
=== END ANALYSIS REPORT ===

=== SKIPPED CHANGES (do not apply; list only) ===
{json.dumps(skipped, indent=2)}
=== END SKIPPED CHANGES ===

Instructions:
1. Apply every change in "changes" to template/docs/conf.py.jinja following
   the skill's Step 2 (mechanical) and Step 3 (judgment) procedures.
2. Check and update ripple-effect files as directed by the skill (Step 5):
   template/docs/requirements.txt, copier.yml, scripts/extract_conf_values.py,
   skills/onboard-existing-docs/references/phase-6-reapply-customizations.md.
3. Never edit anything listed under "SKIPPED CHANGES".
4. Run `bash tests/test_build.sh full` and `bash tests/test_build.sh minimal`
   to confirm the template still builds. Fix any failures you introduced.
5. Do not create a git commit yourself; leave changes unstaged in the working
   tree for the workflow to commit.
6. Write your PR summary (using the skill's Step 7 template) to
   {SUMMARY_OUTPUT_PATH} as the last thing you do.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis_json", help="Path to analyze_conf_diff.py output")
    parser.add_argument("--skill", default=DEFAULT_SKILL_PATH)
    args = parser.parse_args()

    analysis_path = Path(args.analysis_json)
    skill_path = Path(args.skill)

    if not analysis_path.exists():
        print(f"Error: {analysis_path} not found", file=sys.stderr)
        sys.exit(1)
    if not skill_path.exists():
        print(f"Error: {skill_path} not found", file=sys.stderr)
        sys.exit(1)

    analysis = json.loads(analysis_path.read_text())
    skill_text = skill_path.read_text()

    if not analysis.get("changes"):
        print(
            "No actionable changes in analysis report; nothing for the agent to do.",
            file=sys.stderr,
        )

    print(build_prompt(skill_text, analysis))


if __name__ == "__main__":
    main()
