---
name: onboard-existing-docs
description: >
  Onboards a downstream documentation repository that already contains
  un-templated versions of the centrally managed files into the Platform
  Engineering documentation files cookiecutter template. Runs a triage script
  to assess effort, links the repo with cruft, resolves conf.py template
  variables, handles verbatim file diffs, and verifies the build.
  WHEN: onboard existing docs, link existing docs to template, cruft link
  existing repo, migrate docs to central template, assess docs onboarding
  effort
license: Apache-2.0
metadata:
  author: Canonical/platform-engineering
  summary: Onboards a downstream docs repo with pre-existing un-templated files into the central cookiecutter template using cruft.
  version: "1.0.0"
  tags:
    - canonical
    - documentation
    - cookiecutter
    - cruft
    - onboarding
    - sphinx
---

# onboard-existing-docs

## Description

This skill onboards a downstream documentation repository that already contains
un-templated versions of the files managed by the
[Platform Engineering documentation files](https://github.com/canonical/platform-engineering-documentation-files)
cookiecutter template. It assesses the effort required, links the repository
with [cruft](https://cruft.github.io/cruft/), resolves the templatized
`docs/conf.py` variables, handles diffs in verbatim files, and verifies the
documentation build.

The work is split into three sequential phases. Execute each phase in order
using `read_file` to load the sub-skill instructions.

## Assumptions

- The downstream repository already contains un-templated versions of the
  centrally managed files (`.readthedocs.yaml`, `docs/conf.py`, `docs/Makefile`,
  `docs/requirements.txt`, `docs/_dev/`, `docs/_templates/`,
  `docs/release-notes/template/`, `docs/.gitignore`).
- The downstream repository is a git repository.
- `pip` and Python 3 are available on the host.
- The user has access to the downstream repository and can push changes.
- The template repository is
  [`canonical/platform-engineering-documentation-files`](https://github.com/canonical/platform-engineering-documentation-files).

---

## Execution order

| Phase | Sub-skill file | Scope |
|---|---|---|
| 1 | [`triage-and-preflight.md`](references/triage-and-preflight.md) | Run triage script, present summary, verify cruft, run `cruft link` |
| 2 | [`resolve-conf-py.md`](references/resolve-conf-py.md) | Extract values from downstream `conf.py`, map to template variables, confirm with user |
| 3 | [`handle-diffs-and-verify.md`](references/handle-diffs-and-verify.md) | Handle verbatim file diffs, flag extras, verify build, document skips |

### Hand-off between phases

Phase 1 establishes shared state that later phases depend on:
- **`repo_path`** — absolute path to the downstream repository
- **`template_commit`** — the commit hash used for `cruft link`
- **`triage_report`** — the full JSON report from the triage script
- **`.cruft.json` path** — the path to the cruft configuration file created by `cruft link`

Carry these values forward into Phases 2 and 3.

---

## Reference files

| File | Purpose |
|---|---|
| [`triage-and-preflight.md`](references/triage-and-preflight.md) | Phase 1: Run the triage script, assess effort, install cruft, link the repo |
| [`resolve-conf-py.md`](references/resolve-conf-py.md) | Phase 2: Extract values from downstream `conf.py`, map to ~20 template variables, confirm mapping |
| [`handle-diffs-and-verify.md`](references/handle-diffs-and-verify.md) | Phase 3: Handle verbatim file diffs, flag extra files, verify build, document skip list |

## Assets

| File | Purpose |
|---|---|
| [`triage_onboarding.py`](assets/triage_onboarding.py) | Python script that diffs downstream files against the template and produces a JSON triage report |

---

## Non-Negotiables

- Never modify the downstream repository without explicit user confirmation.
- Always run the triage script first, before any other action.
- Always verify the documentation build (`make install && make html`) after
  completing the onboarding.
- Never skip the `docs/conf.py` manual mapping step — do not attempt to
  auto-parse and reverse-engineer template variable values.
- Never run `cruft update` without first confirming the user is ready.
- If a file is added to the `.cruft.json` skip list, always remind the user
  that the file will no longer receive future template updates.

## Mandatory Questions

Ask these unless the answer is already explicit and reliable in the conversation:

- What is the absolute path to the downstream repository?
- Which template commit should I link against? (Accept the latest, or specify a
  hash matching the current state of the downstream files.)
- For each `docs/conf.py` template variable mapping, confirm the extracted value
  is correct.
- For each verbatim file with a diff, confirm: accept the template version,
  keep the downstream version (add to skip list), or manually merge?
- Confirm the documentation build passes after onboarding.

## Stop Early

Stop and explain why if any of these are true:

- The downstream repository does not contain any of the expected files (triage
  report shows all `missing`).
- `cruft link` fails and cannot be resolved.
- The user cannot confirm the `docs/conf.py` variable mappings.
- The documentation build fails after onboarding and cannot be fixed within the
  scope of this skill.
- The downstream repository is not a git repository.