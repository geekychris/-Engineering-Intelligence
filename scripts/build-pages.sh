#!/usr/bin/env bash
set -euo pipefail

# Assembles a GitHub Pages-ready directory from build/ outputs.
#   - Copies engineering-intelligence.{pdf,html,epub} into site/
#   - Generates a small index.html landing page
# Usage: scripts/build-pages.sh [BUILD_DIR] [SITE_DIR]

BUILD_DIR="${1:-build}"
SITE_DIR="${2:-site}"

for artifact in engineering-intelligence.pdf engineering-intelligence.html engineering-intelligence.epub; do
  if [[ ! -f "${BUILD_DIR}/${artifact}" ]]; then
    echo "Missing ${BUILD_DIR}/${artifact}. Run 'make all' first." >&2
    exit 1
  fi
done

rm -rf "${SITE_DIR}"
mkdir -p "${SITE_DIR}"

cp "${BUILD_DIR}/engineering-intelligence.pdf"  "${SITE_DIR}/"
cp "${BUILD_DIR}/engineering-intelligence.html" "${SITE_DIR}/"
cp "${BUILD_DIR}/engineering-intelligence.epub" "${SITE_DIR}/"
[[ -f "${BUILD_DIR}/manifest.json" ]] && cp "${BUILD_DIR}/manifest.json" "${SITE_DIR}/"

# Tell Jekyll to leave the site alone (files starting with _ etc.)
touch "${SITE_DIR}/.nojekyll"

pdf_bytes=$(wc -c <"${SITE_DIR}/engineering-intelligence.pdf" | tr -d ' ')
html_bytes=$(wc -c <"${SITE_DIR}/engineering-intelligence.html" | tr -d ' ')
epub_bytes=$(wc -c <"${SITE_DIR}/engineering-intelligence.epub" | tr -d ' ')

pdf_mb=$(awk "BEGIN { printf \"%.1f\", ${pdf_bytes}/1048576 }")
html_mb=$(awk "BEGIN { printf \"%.1f\", ${html_bytes}/1048576 }")
epub_mb=$(awk "BEGIN { printf \"%.1f\", ${epub_bytes}/1048576 }")

build_date=$(date -u +"%Y-%m-%d")
commit_sha="${GITHUB_SHA:-$(git rev-parse HEAD 2>/dev/null || echo unknown)}"
short_sha="${commit_sha:0:7}"

cat >"${SITE_DIR}/index.html" <<HTML
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Engineering Intelligence &mdash; Downloads</title>
  <style>
    :root { color-scheme: light dark; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      max-width: 42rem;
      margin: 4rem auto;
      padding: 0 1.5rem;
      line-height: 1.55;
    }
    h1 { margin-bottom: 0.25rem; }
    .tagline { color: #666; margin-top: 0; }
    ul.editions { list-style: none; padding: 0; }
    ul.editions li {
      margin: 0.75rem 0;
      padding: 1rem 1.25rem;
      border: 1px solid #ccc;
      border-radius: 8px;
    }
    ul.editions a { font-weight: 600; text-decoration: none; }
    ul.editions a:hover { text-decoration: underline; }
    .meta { color: #888; font-size: 0.85rem; margin-left: 0.5rem; }
    footer { margin-top: 3rem; color: #888; font-size: 0.85rem; }
  </style>
</head>
<body>
  <h1>Engineering Intelligence</h1>
  <p class="tagline">A Quantitative Framework for Measuring, Understanding, and Optimizing Modern Software Engineering.</p>

  <h2>Editions</h2>
  <ul class="editions">
    <li>
      <a href="engineering-intelligence.pdf">PDF</a>
      <span class="meta">${pdf_mb} MB &middot; renders in your browser</span>
    </li>
    <li>
      <a href="engineering-intelligence.html">HTML (single file)</a>
      <span class="meta">${html_mb} MB</span>
    </li>
    <li>
      <a href="engineering-intelligence.epub">EPUB</a>
      <span class="meta">${epub_mb} MB</span>
    </li>
  </ul>

  <footer>
    Built ${build_date} from commit <code>${short_sha}</code>.
    Source: <a href="https://github.com/geekychris/-Engineering-Intelligence">geekychris/-Engineering-Intelligence</a>.
  </footer>
</body>
</html>
HTML

echo "Assembled Pages site at ${SITE_DIR}/"
ls -lh "${SITE_DIR}/"
