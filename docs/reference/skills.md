# Skills

This repository includes a `skills/` directory containing AI skills to assist in common tasks related to this solution.

## Onboarding a repository with preexisting files

The `onboard-existing-docs` skill onboards a downstream repository that already has documentation
tooling files contained in this solution.

The skill uses a multi-phase approach to audit the existing files, runs Copier to generate the solution's scaffold, and re-applies the the repository's customizations.

### Assumptions

- The downstream repository has Python 3.10+, Git 2.27+, and Copier installed.
- Documentation already lives in `docs/` in the downstream repository.
- The downstream repo contains unmanaged copies of one or more files that
  overlap with the template's generated output.

See also: [`skills/onboard-existing-docs/SKILL.md`](../../skills/onboard-existing-docs/SKILL.md)
