# Opinions in this solution

The development of this solution took place over roughly six months starting from the initial conversations and brainstorming. The ideation phase revealed that the solution would have to include opinions about the design and update workflow to accommodate the needs of the Platform Engineering team documentation sets.

## Why Copier?

While developing this solution, two different tools were considered: Cruft and Copier. 
We chose [Copier](https://copier.readthedocs.io/) for the following reasons:

* **Lower operational complexity**: We discovered that Copier needed fewer caveats and workarounds for the solution.

* **Alignment with goals**: Copier aligned better with the needs of this solution, which requires managing files identical across all downstream repositories alongside customized files.

* **More automation-friendly**: Developing the [`onboard-existing-docs` skill](../../skills/onboard-existing-docs/SKILL.md) revealed that Copier better supports a stable and reproducible process. We knew that the solution would need to support onboarding of repositories with existing documentation files, making Copier an ideal candidate.

## Why the Canonical Sphinx Stack?

The target repositories for this solution are ones maintained by the Platform Engineering team at Canonical. We use the [Sphinx Stack](https://documentation.ubuntu.com/sphinx-stack/latest/) as the underlying scaffolding, tooling, and theming for our documentation projects.

## File types

Files in the template fall into two categories:

- **Static files** are assumed to be identical across all downstream repositories. They typically contain no project-specific values.
- **Templated files** (using the `.jinja` suffix) are rendered with project-specific values
  from `.copier-answers.yml` at generation time.

## Single source of truth

The primary purpose of this solution is to act as a single source of truth for the shared documentation files. This solution handles all additions, modifications, removals, and dependency updates across our entire portfolio. The benefits are immeasurable: 

* Renovate noise is reduced in the downstream repositories. A single pull request from Renovate handles a dependency update in this solution, and a single pull request in the downstream repository handles multiple dependency updates within the update frequency.
* We maintain consistency in styling and tooling across our repositories, relying on an automated process rather than manual updates. Repositories no longer fall through the cracks.
* We can introduce common documentation (e.g., contributing guidelines) into all repositories.
