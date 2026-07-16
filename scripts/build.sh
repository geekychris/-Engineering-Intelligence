#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-all}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT/build"
WORK_DIR="$ROOT/.build-src"
BOOK="$ROOT/book.adoc"
PDF_THEME="$ROOT/themes/engineering-intelligence-theme.yml"

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

if [[ "$MODE" == "pdf" || "$MODE" == "all" || "$MODE" == "validate" ]]; then
  [[ -f "$PDF_THEME" ]] || fail "PDF theme was not found"
fi

mkdir -p "$BUILD_DIR"
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

validate_sources() {
  python3 "$ROOT/scripts/validate_sources.py" "$ROOT"
}

clean_edition_outputs() {
  if [[ "$MODE" != "diagrams" ]]; then
    rm -f \
      "$BUILD_DIR/engineering-intelligence.html" \
      "$BUILD_DIR/engineering-intelligence.pdf" \
      "$BUILD_DIR/manifest.json"
  fi
}

render_diagrams() {
  local source output
  local final_dir="$BUILD_DIR/figures/mermaid"
  local staging_dir="$BUILD_DIR/figures/.mermaid-staging"

  rm -rf "$staging_dir"
  mkdir -p "$staging_dir"

  # Render the complete set into a staging directory. The published directory
  # is replaced only after every Mermaid source succeeds, preventing partial or
  # stale figure sets when a source is removed, renamed, or fails to render.
  while IFS= read -r -d '' source; do
    output="$staging_dir/$(basename "${source%.mmd}.svg")"
    npx --no-install mmdc \
      --input "$source" \
      --output "$output" \
      --backgroundColor transparent \
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

  rm -rf "$final_dir"
  mv "$staging_dir" "$final_dir"
}

prepare_sources() {
  cp "$ROOT/book.adoc" "$WORK_DIR/book.adoc"
  cp -R "$ROOT/frontmatter" "$WORK_DIR/frontmatter"
  cp -R "$ROOT/chapters" "$WORK_DIR/chapters"
  cp -R "$ROOT/appendices" "$WORK_DIR/appendices"

  if [[ -d "$ROOT/themes" ]]; then
    cp -R "$ROOT/themes" "$WORK_DIR/themes"
  fi

  mkdir -p "$WORK_DIR/figures/mermaid"

  if compgen -G "$BUILD_DIR/figures/mermaid/*.svg" >/dev/null; then
    cp "$BUILD_DIR"/figures/mermaid/*.svg "$WORK_DIR/figures/mermaid/"
  fi

  python3 - "$WORK_DIR" <<'PY'
from pathlib import Path
import sys

work = Path(sys.argv[1])
for path in work.rglob("*.adoc"):
    text = path.read_text(encoding="utf-8")
    text = text.replace(".mmd[", ".svg[")
    path.write_text(text, encoding="utf-8")
PY
}

build_html() {
  bundle exec asciidoctor \
    --failure-level WARN \
    --safe-mode safe \
    --attribute reproducible \
    --attribute linkcss! \
    --attribute data-uri \
    --destination-dir "$BUILD_DIR" \
    --out-file engineering-intelligence.html \
    "$WORK_DIR/book.adoc"
}

build_pdf() {
  bundle exec asciidoctor-pdf \
    --failure-level WARN \
    --safe-mode safe \
    --attribute reproducible \
    --attribute pdf-themesdir="$WORK_DIR/themes" \
    --attribute pdf-theme=engineering-intelligence \
    --destination-dir "$BUILD_DIR" \
    --out-file engineering-intelligence.pdf \
    "$WORK_DIR/book.adoc"
}

write_manifest() {
  python3 - "$ROOT" "$BUILD_DIR" <<'PY'
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import subprocess
import sys

root = Path(sys.argv[1])
build = Path(sys.argv[2])


def digest(path):
    h = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


try:
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
except Exception:
    commit = os.environ.get("GITHUB_SHA", "unknown")

files = []
for name in ("engineering-intelligence.html", "engineering-intelligence.pdf"):
    path = build / name
    if path.exists():
        files.append(
            {
                "name": name,
                "bytes": path.stat().st_size,
                "sha256": digest(path),
            }
        )

manifest = {
    "title": "Engineering Intelligence",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "source_commit": commit,
    "files": files,
    "diagram_count": len(list((build / "figures" / "mermaid").glob("*.svg"))),
}
(build / "manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
)
PY
}

validate_sources
clean_edition_outputs

case "$MODE" in
  validate)
    render_diagrams
    prepare_sources
    build_html
    build_pdf
    write_manifest
    ;;
  diagrams)
    render_diagrams
    ;;
  html)
    render_diagrams
    prepare_sources
    build_html
    write_manifest
    ;;
  pdf)
    render_diagrams
    prepare_sources
    build_pdf
    write_manifest
    ;;
  all)
    render_diagrams
    prepare_sources
    build_html
    build_pdf
    write_manifest
    ;;
esac

printf 'Publication build completed: %s\n' "$MODE"
