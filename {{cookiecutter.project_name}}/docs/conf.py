import datetime
import os
import textwrap

# Configuration for the Sphinx documentation builder.
# All configuration specific to your project should be done in this file.
#
# A complete list of built-in Sphinx configuration values:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
#
# The Sphinx Stack uses the Canonical Sphinx theme to keep all documentation consistent
# and on brand:
# https://github.com/canonical/canonical-sphinx

#######################
# Project information #
#######################

# Project name
project = "{{ cookiecutter.project_name }}"

# Author name; used in the default copyright statement in the page footer
author = "{{ cookiecutter.author }}"

# The year in the copyright statement
copyright = f"{datetime.date.today().year}"

# Sidebar documentation title
# To disable the title, set it to an empty string.
html_title = project + " documentation"

# Documentation website URL
ogp_site_url = os.environ.get("READTHEDOCS_CANONICAL_URL", "/")

# Preview name of the documentation website
ogp_site_name = "{{ cookiecutter.ogp_site_name }}"

# Preview image URL
ogp_image = "{{ cookiecutter.ogp_image }}"
{% if cookiecutter.html_favicon %}
# Product favicon; shown in bookmarks, browser tabs, etc.
html_favicon = "{{ cookiecutter.html_favicon }}"
{% endif %}
# Dictionary of values to pass into the Sphinx context for all pages:
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_context
html_context = {
    # Product page URL; can be different from product docs URL
    "product_page": "{{ cookiecutter.product_page }}",
{% if cookiecutter.product_tag %}
    # Product tag image; the orange part of your logo, shown in the page header
    "product_tag": "{{ cookiecutter.product_tag }}",
{% endif %}
    # Your Discourse instance URL
    "discourse": "{{ cookiecutter.discourse }}",
    # Your Mattermost channel URL
    "mattermost": "{{ cookiecutter.mattermost }}",
    # Your Matrix channel URL
    "matrix": "{{ cookiecutter.matrix }}",
    # Your documentation GitHub repository URL
    "github_url": "{{ cookiecutter.github_url }}",
    # Docs branch in the repo; used in links for viewing the source files
    "repo_default_branch": "{{ cookiecutter.repo_default_branch }}",
    # Docs location in the repo; used in links for viewing the source files
    "repo_folder": "{{ cookiecutter.repo_folder }}",
{% if cookiecutter.sequential_nav %}
    # Previous / Next buttons at the bottom of pages
    # Valid options: none, prev, next, both
    "sequential_nav": "{{ cookiecutter.sequential_nav }}",
{% endif %}
    # Enable listing contributors on individual pages
    "display_contributors": {{ cookiecutter.display_contributors }},
    # Required for feedback button
    "github_issues": "enabled",
    # Passes the top-level 'author' value to the theme
    "author": author,
    # Documentation license information
    "license": {
        "name": "{{ cookiecutter.license_name }}",
        "url": "{{ cookiecutter.license_url }}",
    },
}
{% if cookiecutter.source_edit_link %}
html_theme_options = {
    "source_edit_link": "{{ cookiecutter.source_edit_link }}",
}
{% endif %}
{% if cookiecutter.slug %}
# Project slug (for documentation hosted on https://documentation.ubuntu.com/)
slug = "{{ cookiecutter.slug }}"
{% endif %}
#######################
# Sitemap configuration: https://sphinx-sitemap.readthedocs.io/
#######################

# Use RTD canonical URL to ensure duplicate pages have a specific canonical URL
html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "/")

# sphinx-sitemap uses html_baseurl to generate the full URL for each page:
sitemap_url_scheme = "{link}"

# Include `lastmod` dates in the sitemap:
sitemap_show_lastmod = True

# Pages excluded from the sitemap:
sitemap_excludes = [
    "404/",
    "genindex/",
    "search/",
]

################################
# Template and asset locations #
################################

# html_static_path = ["_static"]
# templates_path = ["_templates"]

#############
# Redirects #
#############

# Add redirects to the 'redirects.txt' file
# https://sphinxext-rediraffe.readthedocs.io/en/latest/

# To set up redirects in the Read the Docs project dashboard:
# https://docs.readthedocs.io/en/stable/guides/redirects.html

rediraffe_redirects = "redirects.txt"

# Strips '/index.html' from destination URLs when building with 'dirhtml'
rediraffe_dir_only = True


############################
# sphinx-llm configuration #
############################

# This description is included in llms.txt to provide some initial context for your
# product docs.
{% if cookiecutter.llms_txt_description %}
llms_txt_description = textwrap.dedent(
    """\
    {{ cookiecutter.llms_txt_description }}
    """
)
{% else %}
llms_txt_description = textwrap.dedent(
    """\
    This is the documentation for {{ cookiecutter.project_name }}.
    """
)
{% endif %}
# The base URL for references built by sphinx-markdown-builder.
if os.environ.get("READTHEDOCS"):
    markdown_http_base = html_baseurl

###########################
# Link checker exceptions #
###########################

# A regex list of URLs that are ignored by 'make linkcheck'
linkcheck_ignore = [
    "http://127.0.0.1:8000",
    "https://github.com",
    r"https://matrix\.to/.*",
    "https://example.com",
    # SourceForge domains often block linkcheck
    r"https://.*\.sourceforge\.(net|io)/.*",
]

# A regex list of URLs where anchors are ignored by 'make linkcheck'
linkcheck_anchors_ignore_for_url = [r"https://github\.com/.*"]

# Give linkcheck multiple tries on failure
linkcheck_retries = 3

########################
# Configuration extras #
########################

# Custom MyST syntax extensions; see
# https://myst-parser.readthedocs.io/en/latest/syntax/optional.html
# NOTE: By default, the following MyST extensions are enabled:
#   - substitution
#   - deflist
#   - linkify
# myst_enable_extensions = set()

# Custom Sphinx extensions; see
# https://www.sphinx-doc.org/en/master/usage/extensions/index.html
extensions = [
    "canonical_sphinx",
    "notfound.extension",
    "sphinx_design",
    "sphinx_rerediraffe",
    "sphinx_reredirects",
    "sphinx_tabs.tabs",
    "sphinxcontrib.jquery",
    "sphinxext.opengraph",
    "sphinx_config_options",
    "sphinx_contributor_listing",
    "sphinx_filtered_toctree",
    "sphinx_llm.txt",
    "sphinx_related_links",
    "sphinx_roles",
    "sphinx_terminal",
    "sphinx_ubuntu_images",
    "sphinx_youtube_links",
    "sphinxcontrib.cairosvgconverter",
    "sphinx_last_updated_by_git",
    "sphinx.ext.intersphinx",
    "sphinx_sitemap",
]

# Excludes files or directories from processing
exclude_patterns = [
    "doc-cheat-sheet*",
    ".venv*",
]
{% if cookiecutter.disable_feedback_button == "True" %}
# Feedback button at the top
disable_feedback_button = True
{% endif %}
{% if cookiecutter.manpages_url %}
# Manpage URL
manpages_url = "{{ cookiecutter.manpages_url }}"
{% endif %}
# Specifies a reST snippet to be prepended to each .rst file
# This defines a :center: role that centers table cell content.
# This defines a :h2: role that styles content for use with PDF generation.
rst_prolog = """
.. role:: center
   :class: align-center
.. role:: h2
    :class: hclass2
.. role:: woke-ignore
    :class: woke-ignore
.. role:: vale-ignore
    :class: vale-ignore
"""

# Configuration for Intersphinx projects
#
# intersphinx_mapping = {
#     "snap": ("https://snapcraft.io/docs/", None),
# }
