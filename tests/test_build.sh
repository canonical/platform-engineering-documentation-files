#!/bin/bash
# Integration test for the platform-engineering-documentation-files Copier template.
#
# Generates a project from the template, injects minimal Sphinx content, and
# runs "make html" to verify the scaffold builds without warnings or errors.
#
# Usage:
#   bash tests/test_build.sh          # runs the "full" scenario (default)
#   bash tests/test_build.sh full     # all fields populated
#   bash tests/test_build.sh minimal  # only required fields

set -euo pipefail

SCENARIO="${1:-full}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FIXTURES_DIR="$SCRIPT_DIR/fixtures"

# ── Validation ──────────────────────────────────────────────────
if [[ "$SCENARIO" != "minimal" && "$SCENARIO" != "full" ]]; then
    echo "ERROR: Unknown scenario '$SCENARIO'. Use 'minimal' or 'full'." >&2
    exit 1
fi

if ! command -v copier &>/dev/null; then
    echo "ERROR: copier is not installed. Install it with: pipx install copier" >&2
    exit 1
fi

# ── Temp directory ──────────────────────────────────────────────
TMPDIR=$(mktemp -d)
cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT

echo "=== Testing scenario: $SCENARIO ==="
echo ""

# ── Step 1: Generate project from template ──────────────────────
echo "--- Generating project from template ---"

# Common data for both scenarios
COMMON_DATA=(
    --data "project=TestProject"
    --data "author=Canonical Ltd."
)

case "$SCENARIO" in
    minimal)
        # Only required fields; all optional fields use defaults (empty/false)
        copier copy --defaults --overwrite --quiet \
            "${COMMON_DATA[@]}" \
            "$REPO_ROOT" "$TMPDIR"
        ;;
    full)
        # Every field populated to exercise all conditional branches
        copier copy --defaults --overwrite --quiet \
            "${COMMON_DATA[@]}" \
            --data "product_page=example.com" \
            --data "discourse=https://discourse.example.com" \
            --data "mattermost=https://chat.example.com" \
            --data "matrix=https://matrix.example.com" \
            --data "github_url=https://github.com/example/test" \
            --data "repo_default_branch=main" \
            --data "repo_folder=/docs/" \
            --data "ogp_image=https://example.com/ogp.png" \
            --data "html_favicon=_static/favicon.png" \
            --data "product_tag=_static/tag.png" \
            --data "license_name=Apache-2.0" \
            --data "license_url=https://www.apache.org/licenses/LICENSE-2.0" \
            --data "display_contributors=true" \
            --data "source_edit_link=https://github.com/example/test/edit/main/docs/" \
            --data "rtd_slug=test-project" \
            --data "llms_txt_description=Documentation for TestProject, a test project" \
            "$REPO_ROOT" "$TMPDIR"
        ;;
esac

echo ""

# ── Step 2: Verify generated files exist ────────────────────────
echo "--- Verifying generated files ---"

required_files=(
    "docs/conf.py"
    "docs/Makefile"
    "docs/requirements.txt"
    ".readthedocs.yaml"
    ".copier-answers.yml"
)

required_dirs=(
    "docs/_dev"
    "docs/_templates"
    "docs/_static"
    "docs/release-notes/template"
)

for f in "${required_files[@]}"; do
    if [[ ! -f "$TMPDIR/$f" ]]; then
        echo "FAIL: Missing expected file: $f" >&2
        exit 1
    fi
    echo "  ✓ $f"
done

for d in "${required_dirs[@]}"; do
    if [[ ! -d "$TMPDIR/$d" ]]; then
        echo "FAIL: Missing expected directory: $d" >&2
        exit 1
    fi
    echo "  ✓ $d/"
done

echo ""

# ── Step 3: Inject minimal Sphinx content ───────────────────────
echo "--- Injecting test content ---"

cp "$FIXTURES_DIR"/*.md "$TMPDIR/docs/"
echo "  ✓ Copied fixtures to docs/"

# Create placeholder files to avoid warnings from optional features:
# - A minimal favicon so html_favicon doesn't warn about missing file
# - An empty rediraffe_redirects so the redirect extension doesn't warn
# - A .git repo so sphinx-last-updated-by-git can get commit dates
touch "$TMPDIR/docs/_static/favicon.png"
touch "$TMPDIR/docs/_static/tag.png"
touch "$TMPDIR/docs/redirects.txt"
git -C "$TMPDIR" init --quiet
git -C "$TMPDIR" add --all
git -C "$TMPDIR" commit --quiet -m "Test content"
echo "  ✓ Created placeholder assets and git repo"

echo ""

# ── Step 4: Build with Sphinx ───────────────────────────────────
echo "--- Building documentation (make html) ---"

# The Makefile's html target already uses --fail-on-warning, so any
# warning will cause a non-zero exit code.
cd "$TMPDIR/docs"
make html

echo ""
echo "=== PASS ($SCENARIO): Build succeeded with no warnings or errors ==="