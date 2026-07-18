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
mkdir -p "$BUILD_DIR/themes" "$BUILD_DIR/figures/mermaid"
cp "$THEME_CSS" "$BUILD_DIR/themes/"
if compgen -G "$ROOT/figures/mermaid/*.mmd" >/dev/null; then
  if compgen -G "$ROOT/build/figures/mermaid/*.png" >/dev/null; then
    cp "$ROOT/build/figures/mermaid"/*.png "$BUILD_DIR/figures/mermaid/"
  fi
fi

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
    --attribute revealjsdir="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0" \
    --attribute stem=latexmath \
    --attribute customcss=themes/engineering-intelligence.css \
    --destination-dir "$BUILD_DIR" \
    --out-file "$base.html" \
    "$src"
  count=$((count + 1))
done

printf 'Built %d deck(s) into %s\n' "$count" "$BUILD_DIR"
