#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DECKS_SRC="$ROOT/decks"
BUILD_DIR="$ROOT/build/decks"
THEME_CSS="$DECKS_SRC/themes/engineering-intelligence.css"

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

command -v ruby >/dev/null 2>&1 || fail "Ruby is required"
command -v bundle >/dev/null 2>&1 || fail "Bundler is required"
[[ -d "$DECKS_SRC" ]] || fail "decks/ directory not found"
[[ -f "$THEME_CSS" ]] || fail "Deck theme CSS was not found"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/themes" "$BUILD_DIR/figures/mermaid" "$BUILD_DIR/figures/plots"
BUILD_STAMP="$(date -u +'%Y-%m-%d %H:%M UTC')"
# Stamp the theme copy so it's obvious in DevTools which build is live.
{
  printf '/* build: %s */\n' "$BUILD_STAMP"
  cat "$THEME_CSS"
  printf '\n.reveal .build-stamp{position:fixed;bottom:6px;left:10px;font-family:Helvetica,sans-serif;font-size:10px;color:#6C371F;background:rgba(245,235,214,0.75);padding:2px 6px;border-radius:2px;pointer-events:none;z-index:1000}\n'
} > "$BUILD_DIR/themes/engineering-intelligence.css"

# Mermaid diagrams — from the last book build.
if compgen -G "$ROOT/build/figures/mermaid/*.png" >/dev/null; then
  cp "$ROOT/build/figures/mermaid"/*.png "$BUILD_DIR/figures/mermaid/"
fi

# Data plots — regenerated in place so decks don't depend on a prior PDF build.
if [[ -f "$ROOT/scripts/render-plots.py" ]]; then
  python3 "$ROOT/scripts/render-plots.py" "$BUILD_DIR/figures/plots"
fi

# Cover art and other top-level figures referenced by the title slide.
find "$ROOT/figures" -maxdepth 1 -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" \) \
  -exec cp {} "$BUILD_DIR/figures/" \;

count=0
for src in "$DECKS_SRC"/*.adoc; do
  [[ -f "$src" ]] || continue
  base="$(basename "$src" .adoc)"
  out="$BUILD_DIR/$base.html"
  # Copy the deck source into the staging area, appending a build stamp
  # slide-footer node so every rendered slide carries a visible marker.
  staged="$BUILD_DIR/.staged-$base.adoc"
  cat "$src" > "$staged"
  bundle exec asciidoctor-revealjs \
    --safe-mode server \
    --base-dir "$ROOT" \
    --attribute revealjs_theme=white \
    --attribute revealjs_hash=true \
    --attribute revealjs_slideNumber="c/t" \
    --attribute revealjs_transition=fade \
    --attribute revealjs_controls=true \
    --attribute revealjs_progress=true \
    --attribute revealjs_center=false \
    --attribute revealjs_history=true \
    --attribute revealjs_width=1280 \
    --attribute revealjs_height=800 \
    --attribute revealjs_margin=0.04 \
    --attribute revealjs_minScale=0.2 \
    --attribute revealjs_maxScale=2.0 \
    --attribute revealjsdir="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0" \
    --attribute stem=latexmath \
    --attribute customcss=themes/engineering-intelligence.css \
    --destination-dir "$BUILD_DIR" \
    --out-file "$base.html" \
    "$src"
  # Inject a fixed-position build-stamp element after <body>.
  python3 - "$out" "$BUILD_STAMP" <<'PY'
import sys, re
path, stamp = sys.argv[1], sys.argv[2]
text = open(path).read()
tag = f'<div class="build-stamp">build: {stamp}</div>'
text = text.replace('<body>', f'<body>{tag}', 1)
open(path, 'w').write(text)
PY
  rm -f "$staged"
  count=$((count + 1))
done

printf 'Built %d deck(s) into %s\n' "$count" "$BUILD_DIR"
