---
name: triage-and-preflight
description: "Phase 1 of the onboard-existing-docs skill. Runs the triage script to assess onboarding effort, verifies cruft is installed, and links the downstream repository to the template."
---

# triage-and-preflight

**Prerequisites:** This is Phase 1 of the `onboard-existing-docs` skill. See the
parent [SKILL.md](../SKILL.md) for assumptions and the full workflow overview.

---

## Instructions

### Step 1: Confirm the downstream repository path

Ask the user for the absolute path to the downstream repository. If the user
has already provided it, confirm it is correct.

Verify the path exists and is a git repository:

```bash
git -C <repo_path> rev-parse --is-inside-work-tree
```

If this fails, stop and tell the user the path must be a git repository.

### Step 2: Run the triage script

Run the triage script against the downstream repository:

```bash
python3 skills/onboard-existing-docs/assets/triage_onboarding.py --repo-path <repo_path>
```

The script is located at `skills/onboard-existing-docs/assets/triage_onboarding.py`
relative to the template repository root.

If the user wants to link against a specific template commit (not the latest),
note the commit hash now — it will be needed in Step 5.

### Step 3: Present the triage summary

Parse the JSON output and present a clear summary to the user. Group files by
status:

| Status | Meaning | Action needed |
|---|---|---|
| `identical` | File matches the template exactly | No action — cruft will track it automatically |
| `minor_diff` | ≤ 5 changed lines | Review in Phase 3; likely version bumps or minor tweaks |
| `major_diff` | > 5 changed lines | Review in Phase 3; likely significant customization |
| `missing` | File doesn't exist downstream | cruft will create it on first update |
| `templated_needs_manual` | `docs/conf.py` — needs variable mapping | Resolved in Phase 2 |
| `error` | File could not be read | Investigate and resolve before proceeding |

Also list any **extra files** detected — these are files in template-managed
directories that are not part of the template. They won't be affected by cruft
but the user should be aware of them.

**Highlight the high-effort items:**
- `templated_needs_manual` (always `docs/conf.py`) — this is the most
  time-consuming step
- `major_diff` files — these will require careful review

Ask the user: **"Based on this assessment, do you want to proceed with onboarding?"**

If the user says no, stop here. If yes, continue to Step 4.

### Step 4: Verify cruft is installed

Check if cruft is available:

```bash
pip show cruft
```

If cruft is not installed, install it:

```bash
pip install cruft
```

Verify the installation:

```bash
cruft --version
```

### Step 5: Check for existing cruft configuration

Check if the downstream repository already has a `.cruft.json` file:

```bash
ls -la <repo_path>/.cruft.json
```

If `.cruft.json` already exists:
- Read it and check the `template` field — it should point to
  `https://github.com/canonical/platform-engineering-documentation-files`.
- If it points to a different template, warn the user. They may be trying to
  re-link to a different template.
- If it already points to the correct template, the repo is already linked.
  Ask the user if they want to re-link (this will overwrite the existing
  `.cruft.json`).

### Step 6: Link the repository with cruft

Run `cruft link` to connect the downstream repository to the template:

```bash
cd <repo_path>
cruft link https://github.com/canonical/platform-engineering-documentation-files
```

If the user specified a particular commit hash in Step 2, pass it with
`--checkout <commit>`:

```bash
cruft link https://github.com/canonical/platform-engineering-documentation-files --checkout <commit>
```

**What this does:** `cruft link` creates a `.cruft.json` file in the downstream
repository that records:
- The template repository URL
- The commit hash the repo is linked against
- The template variables (cookiecutter context) — initially empty or defaulted

**Handle errors:**
- If cruft complains the directory is not empty: this is expected — confirm
  with the user that they want to link an existing repo.
- If cruft fails with a git error: check that the downstream repo is clean
  (no uncommitted changes) and try again.
- If cruft cannot find the template: verify the URL is correct and the user
  has network access.

### Step 7: Confirm the link was created

Verify `.cruft.json` exists and contains the expected template URL:

```bash
cat <repo_path>/.cruft.json
```

Confirm the `template` field is
`https://github.com/canonical/platform-engineering-documentation-files`.

### Step 8: Hand off to Phase 2

Record the following values for use in Phase 2:
- **`repo_path`**: absolute path to the downstream repository
- **`template_commit`**: the commit hash recorded in `.cruft.json`
- **`triage_report`**: the full JSON output from Step 2

Proceed to [`resolve-conf-py.md`](resolve-conf-py.md).