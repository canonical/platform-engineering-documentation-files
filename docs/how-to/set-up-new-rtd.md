# How to set up a new RTD project

After generating the documentation scaffold with Copier, your repository
includes a `.readthedocs.yaml` that configures how Read the Docs builds
your documentation. This guide covers what the template provides and how
to verify everything works.

## What the template generates

The `.readthedocs.yaml` file is a static file — it's identical across all
downstream repos. It configures:

- **Build environment**: Ubuntu 22.04, Python 3.11
- **Sphinx builder**: `dirhtml` (directory-based HTML)
- **Fail on warning**: Builds fail if Sphinx emits warnings
- **PDF output**: Enabled alongside HTML
- **Python dependencies**: Installed from `docs/requirements.txt`
- **PR optimisation**: Skips building pull requests that don't touch the
  `docs/` directory or `.readthedocs.yaml`

## Copier variables that affect RTD

Two Copier variables are specific to Read the Docs:

| Variable | Purpose |
|---|---|
| `rtd_slug` | Your Read the Docs project slug. Only needed if hosted on `documentation.ubuntu.com`. Leave empty otherwise. |
| `old_domain` | Old RTD domain to redirect from (e.g., `canonical-discourse-k8s-charm.readthedocs-hosted.com`). Leave empty to skip link rewriting. |

These values are written into `.copier-answers.yml` and used by the
`overwrite_links.js` script in the generated `docs/_static/js/` directory
to handle domain redirects.

## Verifying the build

After generating the scaffold and pushing to your repository:

1. Ensure your RTD project is configured to build from your repository.
   (This step happens in the RTD web UI — it's outside the scope of this template.)
2. Trigger a build on Read the Docs.
3. Confirm the build completes without errors.
4. Verify that the generated site renders correctly, including the header,
   footer, and any community links you configured.

## Troubleshooting

- **Build fails with Sphinx warnings**: Check the build log for the specific
  warning. The template sets `fail_on_warning: true`, so any Sphinx warning
  will fail the build.
- **Missing community links**: Verify your `discourse`, `mattermost`, `matrix`,
  and `github_url` values in `.copier-answers.yml`, then re-run `copier update`.
- **Domain redirects not working**: Confirm `old_domain` is set correctly in
  `.copier-answers.yml`.
