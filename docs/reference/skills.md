# Skills

This repository includes a `skills/` directory containing AI skills to assist in common tasks related to this solution.

## Onboarding a repository with preexisting files

The `onboard-existing-docs` skill onboards a downstream repository that already has documentation
tooling files contained in this solution.

The skill uses a multi-phase approach to audit the existing files, runs Copier to generate the
solution's scaffold, and re-applies the repository's customizations.

### Assumptions

- The downstream repository has Python 3.10+, Git 2.27+, and Copier installed.
- Documentation already lives under `docs/` in the downstream repository.
- The downstream repository contains unmanaged copies of one or more files that
  overlap with the template's generated output.

See also: [`skills/onboard-existing-docs/SKILL.md`](../../skills/onboard-existing-docs/SKILL.md)

## Syncing updates for `conf.py`

The `update-conf-py` skill applies upstream `canonical/sphinx-stack` `conf.py` changes to
this solution's templated `template/docs/conf.py.jinja`.

The skill consumes a deterministic JSON report produced by `scripts/analyze_conf_diff.py`,
applies high-confidence changes mechanically, and makes judgment calls for flagged changes
while respecting intentional divergences. It is invoked from the `analyze-conf-py` job in the
`sphinx-stack-sync` workflow.

### Assumptions

- The `analyze_conf_diff.py` script has already produced an `analysis.json` report comparing
  two upstream `sphinx-stack` versions.
- The divergence manifest (`scripts/conf_divergences.json`) and section map
  (`scripts/conf_section_map.json`) are available and up to date.

See also: [`skills/update-conf-py/SKILL.md`](../../skills/update-conf-py/SKILL.md)
