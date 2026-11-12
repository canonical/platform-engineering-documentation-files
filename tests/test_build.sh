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
# - A real rediraffe redirect (old-reference -> reference) so the redirect
#   extension is exercised rather than just loaded
# - A .git repo so sphinx-last-updated-by-git can get commit dates
touch "$TMPDIR/docs/_static/favicon.png"
touch "$TMPDIR/docs/_static/tag.png"
echo "old-reference reference" > "$TMPDIR/docs/redirects.txt"
git -C "$TMPDIR" init --quiet
git -C "$TMPDIR" add --all
git -C "$TMPDIR" -c user.name="Test Build" -c user.email="test-build@example.invalid" commit --quiet -m "Test content"
echo "  ✓ Created placeholder assets and git repo"

echo ""

# ── Step 4: Build with Sphinx ───────────────────────────────────
echo "--- Building documentation (make html) ---"

# The Makefile's html target already uses --fail-on-warning, so any
# warning will cause a non-zero exit code.
cd "$TMPDIR/docs"
make html

echo ""

# ── Step 5: Assert expected output artifacts ────────────────────
echo "--- Verifying build output artifacts ---"

BUILD_DIR="$TMPDIR/docs/_build"

# assert_file <path> <description>
assert_file() {
    if [[ ! -f "$1" ]]; then
        echo "FAIL: Expected artifact missing: $2 ($1)" >&2
        exit 1
    fi
    echo "  ✓ $2"
}

# assert_grep <pattern> <file> <description>
assert_grep() {
    if ! grep -q "$1" "$2" 2>/dev/null; then
        echo "FAIL: Expected content not found: $3 (pattern '$1' in $2)" >&2
        exit 1
    fi
    echo "  ✓ $3"
}

# Core generated files
assert_file "$BUILD_DIR/llms.txt" "sphinx-llm generated llms.txt"
assert_file "$BUILD_DIR/doc-sitemap.xml" "sphinx-sitemap generated doc-sitemap.xml"
assert_file "$BUILD_DIR/404/index.html" "sphinx-notfound-page generated 404 page"
assert_file "$BUILD_DIR/old-reference/index.html" "rediraffe generated redirect page"

# Sitemap references the built pages
assert_grep "reference" "$BUILD_DIR/doc-sitemap.xml" "sitemap includes the reference page URL"

# Mermaid diagrams rendered on the extensions page
assert_grep "mermaid" "$BUILD_DIR/extensions/index.html" "mermaid diagram rendered"
assert_grep "C4Context" "$BUILD_DIR/extensions/index.html" "C4Context mermaid diagram rendered"

# OpenGraph metadata injected into the page head
assert_grep 'property="og:' "$BUILD_DIR/index.html" "sphinxext-opengraph injected og: meta tags"

# Extension-specific output on the extensions page
EXT_PAGE="$BUILD_DIR/extensions/index.html"
assert_grep "sd-card" "$EXT_PAGE" "sphinx-design card rendered"
assert_grep "sphinx-tabs" "$EXT_PAGE" "sphinx-tabs rendered"
assert_grep "terminal" "$EXT_PAGE" "sphinx-terminal rendered"
assert_grep "youtube_link" "$EXT_PAGE" "sphinx-youtube-links rendered"
assert_grep "relatedlinks" "$EXT_PAGE" "sphinx-related-links rendered"

echo ""

# ── Step 6: Assert the warnings log is empty ────────────────────
echo "--- Verifying warnings log is empty ---"

WARNINGS_FILE="$TMPDIR/docs/_dev/warnings.txt"
if [[ -s "$WARNINGS_FILE" ]]; then
    echo "FAIL: Sphinx produced warnings:" >&2
    cat "$WARNINGS_FILE" >&2
    exit 1
fi
echo "  ✓ No warnings recorded in $WARNINGS_FILE"

echo ""

# ── Step 7 (optional): Check external links ─────────────────────
# Opt-in because it depends on external network availability and third-party
# sites; intended to run as a separate, non-blocking CI job. Validates the
# template's linkcheck configuration and the intersphinx mapping.
if [[ "${RUN_LINKCHECK:-0}" == "1" ]]; then
    echo "--- Checking external links (make linkcheck) ---"
    make linkcheck
    echo "  ✓ Link check completed"
    echo ""
fi

echo "=== PASS ($SCENARIO): Build succeeded with no warnings or errors ==="