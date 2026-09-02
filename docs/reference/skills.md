# Skills in this repository

This repository includes AI-assisted skills that automate common workflows.
Skills are defined in the `skills/` directory and are designed to be used
with an AI coding agent.

## `onboard-existing-docs`

**Location:** [`skills/onboard-existing-docs/SKILL.md`](../../skills/onboard-existing-docs/SKILL.md)

Onboards a downstream repository that already has unmanaged documentation
tooling files (Sphinx config, Makefile, requirements, and so on) into the
Copier-based management solution.

### What it does

- Audits the existing documentation tooling files
- Extracts project-specific values from the existing `docs/conf.py`
- Identifies downstream-only customizations to preserve
- Backs up and removes overlapping tooling files
- Runs Copier to generate the scaffold
- Re-applies downstream customizations
- Validates the build

### Assumptions

- The downstream repository has Python 3.10+, Git 2.27+, and Copier installed.
- Documentation already lives in `docs/` in the downstream repository.
- The downstream repo contains unmanaged copies of one or more files that
  overlap with the template's generated output.

### Phase-by-phase workflow

The skill runs through eight sequential phases:

| Phase | File | What happens |
|---|---|---|
| 1 | [`phase-1-audit.md`](../../skills/onboard-existing-docs/references/phase-1-audit.md) | Audits the downstream repo for files that overlap with the template |
| 2 | [`phase-2-extract-values.md`](../../skills/onboard-existing-docs/references/phase-2-extract-values.md) | Extracts project-specific values from the existing `docs/conf.py` |
| 3 | [`phase-3-identify-customizations.md`](../../skills/onboard-existing-docs/references/phase-3-identify-customizations.md) | Identifies downstream-only customizations to preserve |
| 4 | [`phase-4-backup-remove.md`](../../skills/onboard-existing-docs/references/phase-4-backup-remove.md) | Backs up and removes overlapping tooling files |
| 5 | [`phase-5-run-copier.md`](../../skills/onboard-existing-docs/references/phase-5-run-copier.md) | Runs Copier to generate the documentation scaffold |
| 6 | [`phase-6-reapply-customizations.md`](../../skills/onboard-existing-docs/references/phase-6-reapply-customizations.md) | Re-applies downstream customizations to the generated files |
| 7 | [`phase-7-validate-commit.md`](../../skills/onboard-existing-docs/references/phase-7-validate-commit.md) | Validates the build and commits the result |
| 8 | [`phase-8-post-onboarding.md`](../../skills/onboard-existing-docs/references/phase-8-post-onboarding.md) | Post-onboarding guidance and next steps |

### How to invoke

Use the skill with an AI coding agent that supports skill execution. Refer to
the [SKILL.md](../../skills/onboard-existing-docs/SKILL.md) file for the full
agent workflow and instructions.
