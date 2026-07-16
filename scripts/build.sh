#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-all}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT/build"
WORK_DIR="$ROOT/.build-src"
RENDER_OUTPUT_DIR="$WORK_DIR/output"
EDITION_STAGING_DIR="$BUILD_DIR/.edition-staging"
DIAGRAM_STAGING_DIR="$BUILD_DIR/figures/.mermaid-staging"
DIAGRAM_FINAL_DIR="$BUILD_DIR/figures/mermaid"
BOOK="$ROOT/book.adoc"
PDF_THEME="$ROOT/themes/engineering-intelligence-theme.yml"
HTML_STYLESHEET="$ROOT/styles/engineering-intelligence.css"
MERMAID_CONFIG="$ROOT/figures/mermaid.config.json"
MATH_RENDERER="$ROOT/scripts/render-math.js"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "$2"
}

case "$MODE" in
  all|html|pdf|validate|diagrams)
    ;;
  *)
    fail "Unknown build mode: $MODE"
    ;;
esac

require_command python3 "Python 3 is required"
require_command node "Node.js is required"
require_command npx "npx is required"

if [[ "$MODE" != "diagrams" ]]; then
  require_command ruby "Ruby is required"
  require_command bundle "Bundler is required"
fi

[[ -f "$BOOK" ]] || fail "book.adoc was not found"
[[ -f "$ROOT/scripts/validate_sources.py" ]] || fail "source validator was not found"
[[ -f "$MERMAID_CONFIG" ]] || fail "Mermaid config was not found"

if [[ "$MODE" != "diagrams" ]]; then
  [[ -f "$MATH_RENDERER" ]] || fail "math renderer was not found"
fi

if [[ "$MODE" == "html" || "$MODE" == "all" || "$MODE" == "validate" ]]; then
  [[ -f "$HTML_STYLESHEET" ]] || fail "HTML stylesheet was not found"
fi

if [[ "$MODE" == "pdf" || "$MODE" == "all" || "$MODE" == "validate" ]]; then
  [[ -f "$PDF_THEME" ]] || fail "PDF theme was not found"
fi

initialize_publication_identity() {
  if [[ -n "${SOURCE_DATE_EPOCH:-}" ]]; then
    [[ "$SOURCE_DATE_EPOCH" =~ ^[0-9]+$ ]] || \
      fail "SOURCE_DATE_EPOCH must be a non-negative integer"
  elif command -v git >/dev/null 2>&1 && git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    SOURCE_DATE_EPOCH="$(git -C "$ROOT" log -1 --format=%ct)"
  else
    SOURCE_DATE_EPOCH="0"
  fi

  if [[ -n "${SOURCE_COMMIT:-}" ]]; then
    :
  elif command -v git >/dev/null 2>&1 && git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    SOURCE_COMMIT="$(git -C "$ROOT" rev-parse HEAD)"
  elif [[ -n "${GITHUB_SHA:-}" ]]; then
    SOURCE_COMMIT="$GITHUB_SHA"
  else
    SOURCE_COMMIT="0000000000000000000000000000000000000000"
  fi

  [[ "$SOURCE_COMMIT" =~ ^[0-9a-f]{40}$ ]] || \
    fail "SOURCE_COMMIT must be a full 40-character lowercase Git SHA"

  export SOURCE_DATE_EPOCH SOURCE_COMMIT
}

initialize_publication_identity

mkdir -p "$BUILD_DIR/figures"
rm -rf "$WORK_DIR" "$EDITION_STAGING_DIR" "$DIAGRAM_STAGING_DIR"
mkdir -p "$WORK_DIR" "$RENDER_OUTPUT_DIR"
if [[ "$MODE" != "diagrams" ]]; then
  mkdir -p "$EDITION_STAGING_DIR"
fi

validate_sources() {
  python3 "$ROOT/scripts/validate_sources.py" "$ROOT"
}

render_diagrams() {
  local source output

  rm -rf "$DIAGRAM_STAGING_DIR"
  mkdir -p "$DIAGRAM_STAGING_DIR"

  # Render Mermaid to high-DPI PNG rather than SVG. Mermaid v11 emits node
  # labels inside <foreignObject> (HTML in SVG), which prawn-svg cannot
  # render, so text disappears from PDF SVGs. Rasterising through mmdc
  # preserves every label at print quality without a bespoke SVG rewriter.
  while IFS= read -r -d '' source; do
    output="$DIAGRAM_STAGING_DIR/$(basename "${source%.mmd}.png")"
    npx --no-install mmdc \
      --input "$source" \
      --output "$output" \
      --backgroundColor transparent \
      --configFile "$MERMAID_CONFIG" \
      --width 2400 \
      --height 1800 \
      --scale 2 \
      --quiet
  done < <(
    python3 - "$ROOT/figures/mermaid" <<'PY'
from pathlib import Path
import os
import sys

source_dir = Path(sys.argv[1])
for path in sorted(source_dir.glob("*.mmd")):
    sys.stdout.buffer.write(os.fsencode(path))
    sys.stdout.buffer.write(b"\0")
PY
  )
}

publish_diagrams() {
  rm -rf "$DIAGRAM_FINAL_DIR"
  mv "$DIAGRAM_STAGING_DIR" "$DIAGRAM_FINAL_DIR"
}

prepare_sources() {
  cp "$ROOT/book.adoc" "$WORK_DIR/book.adoc"
  cp -R "$ROOT/frontmatter" "$WORK_DIR/frontmatter"
  cp -R "$ROOT/chapters" "$WORK_DIR/chapters"
  cp -R "$ROOT/appendices" "$WORK_DIR/appendices"

  if [[ -d "$ROOT/themes" ]]; then
    cp -R "$ROOT/themes" "$WORK_DIR/themes"
  fi

  if [[ -d "$ROOT/styles" ]]; then
    cp -R "$ROOT/styles" "$WORK_DIR/styles"
  fi

  mkdir -p "$WORK_DIR/figures/mermaid"

  if compgen -G "$DIAGRAM_STAGING_DIR/*.png" >/dev/null; then
    cp "$DIAGRAM_STAGING_DIR"/*.png "$WORK_DIR/figures/mermaid/"
  fi

  python3 - "$WORK_DIR" <<'PY'
from pathlib import Path
import sys

work = Path(sys.argv[1])
for path in work.rglob("*.adoc"):
    text = path.read_text(encoding="utf-8")
    text = text.replace(".mmd[", ".png[")
    # Chapter files reference figures with '../figures/...' so they render
    # standalone in the source tree. In the staged jail, book.adoc is the
    # top-level document and figures live alongside it, so any '../' in an
    # image target escapes the jail and asciidoctor emits a warning.
    text = text.replace("image::../figures/", "image::figures/")
    path.write_text(text, encoding="utf-8")
PY
}

render_math() {
  # Pre-render every stem:[...] and [stem] block into an SVG under
  # figures/math/ inside the jail and rewrite the source to reference it.
  # asciidoctor-pdf's built-in stem handling is unavailable in safe mode
  # without the mathematical gem, and MathJax is a browser-only runtime,
  # so precomputing SVGs is the portable path for both HTML and PDF.
  node "$MATH_RENDERER" "$WORK_DIR"
}

build_html() {
  local output="$RENDER_OUTPUT_DIR/engineering-intelligence.html"
  rm -f "$output"
  bundle exec asciidoctor \
    --failure-level WARN \
    --safe-mode safe \
    --attribute reproducible \
    --attribute linkcss! \
    --attribute data-uri \
    --attribute stylesdir="$WORK_DIR/styles" \
    --attribute stylesheet=engineering-intelligence.css \
    --destination-dir "$RENDER_OUTPUT_DIR" \
    --out-file engineering-intelligence.html \
    "$WORK_DIR/book.adoc"
  mv "$output" "$EDITION_STAGING_DIR/engineering-intelligence.html"
}

build_pdf() {
  local output="$RENDER_OUTPUT_DIR/engineering-intelligence.pdf"
  rm -f "$output"
  bundle exec asciidoctor-pdf \
    --failure-level WARN \
    --safe-mode safe \
    --attribute reproducible \
    --attribute pdf-themesdir="$WORK_DIR/themes" \
    --attribute pdf-theme=engineering-intelligence \
    --destination-dir "$RENDER_OUTPUT_DIR" \
    --out-file engineering-intelligence.pdf \
    "$WORK_DIR/book.adoc"
  mv "$output" "$EDITION_STAGING_DIR/engineering-intelligence.pdf"
}

write_manifest() {
  python3 - "$EDITION_STAGING_DIR" "$DIAGRAM_STAGING_DIR" "$MODE" <<'PY'
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import sys

editions = Path(sys.argv[1])
diagrams = Path(sys.argv[2])
build_mode = sys.argv[3]


def digest(path):
    h = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


commit = os.environ["SOURCE_COMMIT"]
epoch = int(os.environ["SOURCE_DATE_EPOCH"])
publication_time = datetime.fromtimestamp(epoch, timezone.utc).isoformat()

files = []
for name in ("engineering-intelligence.html", "engineering-intelligence.pdf"):
    path = editions / name
    if path.exists():
        files.append(
            {
                "name": name,
                "bytes": path.stat().st_size,
                "sha256": digest(path),
            }
        )

manifest = {
    "schema_version": 1,
    "title": "Engineering Intelligence",
    "build_mode": build_mode,
    "publication_time": publication_time,
    "source_date_epoch": epoch,
    "source_commit": commit,
    "files": files,
    "diagram_count": len(list(diagrams.glob("*.png"))),
}
(editions / "manifest.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
PY
}

publish_publication() {
  local name

  publish_diagrams

  for name in engineering-intelligence.html engineering-intelligence.pdf; do
    if [[ -f "$EDITION_STAGING_DIR/$name" ]]; then
      mv -f "$EDITION_STAGING_DIR/$name" "$BUILD_DIR/$name"
    else
      rm -f "$BUILD_DIR/$name"
    fi
  done
  mv -f "$EDITION_STAGING_DIR/manifest.json" "$BUILD_DIR/manifest.json"
  rmdir "$EDITION_STAGING_DIR"
}

validate_sources

case "$MODE" in
  validate)
    render_diagrams
    prepare_sources
    render_math
    build_html
    build_pdf
    write_manifest
    publish_publication
    ;;
  diagrams)
    render_diagrams
    publish_diagrams
    ;;
  html)
    render_diagrams
    prepare_sources
    render_math
    build_html
    write_manifest
    publish_publication
    ;;
  pdf)
    render_diagrams
    prepare_sources
    render_math
    build_pdf
    write_manifest
    publish_publication
    ;;
  all)
    render_diagrams
    prepare_sources
    render_math
    build_html
    build_pdf
    write_manifest
    publish_publication
    ;;
esac

printf 'Publication build completed: %s\n' "$MODE"
