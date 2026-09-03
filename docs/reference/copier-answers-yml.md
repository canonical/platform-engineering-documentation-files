# Variables used by Copier

The variables defined in `copier.yml` provide the ability to customize
the files in this solution based on the downstream repository. 
These variables are prompted during `copier copy` and stored in the downstream
repository's `.copier-answers.yml`.

## Core identity

| Variable | Type | Default | Help | Used in |
|---|---|---|---|---|
| `project` | `str` | `"Project"` | Official name of your project or product (for example, "Ubuntu Server") | `docs/conf.py` |
| `author` | `str` | `"Canonical Ltd."` | Author name used in the copyright footer | `docs/conf.py` |

## URLs & community

| Variable | Type | Default | Help | Used in |
|---|---|---|---|---|
| `product_page` | `str` | `""` | Product website URL without the `https://` prefix (for example, `ubuntu.com/lxd`). Leave empty if none. | `docs/conf.py` |
| `discourse` | `str` | `""` | Your Discourse instance URL. Leave empty if none. | `docs/conf.py` |
| `mattermost` | `str` | `""` | Your Mattermost channel URL. Leave empty if none. | `docs/conf.py` |
| `matrix` | `str` | `""` | Your Matrix channel URL. Leave empty if none. | `docs/conf.py` |
| `github_url` | `str` | `""` | GitHub repository URL for "Edit on GitHub" links and issue reporting. Leave empty to disable. | `docs/conf.py` |
| `repo_default_branch` | `str` | `"main"` | Default branch name of your repository | `docs/conf.py` |
| `repo_folder` | `str` | `"/docs/"` | Path to the docs folder within your repository | `docs/conf.py` |

## Branding

| Variable | Type | Default | Help | Used in |
|---|---|---|---|---|
| `ogp_image` | `str` | `"https://assets.ubuntu.com/v1/cc828679-docs_illustration.svg"` | URL for the social preview (Open Graph) image | `docs/conf.py` |
| `html_favicon` | `str` | `""` | Path to a custom favicon (for example, `_static/favicon.png`). Leave empty to use the default. | `docs/conf.py` |
| `product_tag` | `str` | `""` | Path to the product tag image shown in the page header (for example, `_static/tag.png`). Leave empty to skip. | `docs/conf.py` |

## License

| Variable | Type | Default | Help | Used in |
|---|---|---|---|---|
| `license_name` | `str` | `""` | SPDX license identifier for your project (for example, `Apache-2.0`, `GPL-3.0`) | `docs/conf.py` |
| `license_url` | `str` | `""` | Direct URL to your project's license statement | `docs/conf.py` |

## Features

| Variable | Type | Default | Help | Used in |
|---|---|---|---|---|
| `display_contributors` | `bool` | `false` | Show a list of contributors on each page? | `docs/conf.py` |
| `source_edit_link` | `str` | `""` | URL for the "Edit on GitHub" link on each page. Leave empty to hide the edit button. | `docs/conf.py` |

## Read the Docs

| Variable | Type | Default | Help | Used in |
|---|---|---|---|---|
| `rtd_slug` | `str` | `""` | Read the Docs project slug (needed if hosted on `canonical.com` or `documentation.ubuntu.com`). Leave empty otherwise. | `docs/_static/js/overwrite_links.js` |
| `old_domain` | `str` | `""` | Old Read the Docs domain to redirect from (for example, `canonical-canonical-charm.readthedocs-hosted.com`). Leave empty to skip link rewriting. | `docs/_static/js/overwrite_links.js` |
