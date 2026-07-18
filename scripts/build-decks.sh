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
cp "$THEME_CSS" "$BUILD_DIR/themes/"

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
  count=$((count + 1))
done

printf 'Built %d deck(s) into %s\n' "$count" "$BUILD_DIR"
