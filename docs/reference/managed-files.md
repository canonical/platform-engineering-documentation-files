# Managed files

This solution manages the following files:

| Area | Files | Type |
|------|-------|------|
| Sphinx configuration | `docs/conf.py` | Templated per project |
| URL domain configuration | `docs/_static/js/overwrite_links.js` | Templated per project |
| Build tooling | `docs/Makefile`, `docs/requirements.txt` | Static |
| Developer tooling | `docs/_dev/` | Static |
| HTML templates | `docs/_templates/` (header, footer) | Static |
| Read the Docs config | `.readthedocs.yaml` | Static |
| Release note templates | `docs/release-notes/template/` | Static |