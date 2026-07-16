#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-all}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT/build"
WORK_DIR="$ROOT/.build-src"
BOOK="$ROOT/book.adoc"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

command -v ruby >/dev/null 2>&1 || fail "Ruby is required"
command -v bundle >/dev/null 2>&1 || fail "Bundler is required"
command -v node >/dev/null 2>&1 || fail "Node.js is required"
command -v npx >/dev/null 2>&1 || fail "npx is required"
command -v python3 >/dev/null 2>&1 || fail "Python 3 is required"
[[ -f "$BOOK" ]] || fail "book.adoc was not found"

mkdir -p "$BUILD_DIR"
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

validate_references() {
  python3 - "$ROOT" <<'PY'
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve()
book = root / "book.adoc"
errors = []
visited = set()

include_re = re.compile(r"include::([^\[]+)\[")
image_re = re.compile(r"image::([^\[]+)\[")
anchor_re = re.compile(r"\[\[([^\],]+)(?:,[^\]]*)?\]\]")
xref_re = re.compile(r"<<([^,>]+)(?:,[^>]*)?>>")
citation_key_re = re.compile(r"^[a-z][a-z0-9-]*\d{4}(?:-[a-z0-9-]+)?$")


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def walk(path: Path):
    path = path.resolve()
    if path in visited:
        return
    visited.add(path)
    if not path.exists():
        errors.append(f"missing included file: {relative(path)}")
        return
    if not path.is_file():
        errors.append(f"included path is not a file: {relative(path)}")
        return

    text = path.read_text(encoding="utf-8")
    for match in include_re.finditer(text):
        raw = match.group(1).strip()
        if "{" in raw or "}" in raw:
            # Attribute-expanded includes cannot be resolved safely by this
            # lightweight validator; Asciidoctor validates them during build.
            continue
        walk((path.parent / raw).resolve())

    for match in image_re.finditer(text):
        raw = match.group(1).strip()
        if raw.startswith(("http://", "https://", "data:")):
            continue
        if "{" in raw or "}" in raw:
            continue
        target = (path.parent / raw).resolve()
        if not target.exists():
            errors.append(
                f"missing image source referenced by {relative(path)}: {raw}"
            )


walk(book)

anchors = {}
citation_references = []
for path in sorted(visited):
    if not path.exists() or path.suffix != ".adoc":
        continue
    text = path.read_text(encoding="utf-8")
    for match in anchor_re.finditer(text):
        key = match.group(1).strip()
        if key in anchors:
            errors.append(
                f"duplicate explicit anchor '{key}' in {relative(path)} and "
                f"{relative(anchors[key])}"
            )
        else:
            anchors[key] = path

    for match in xref_re.finditer(text):
        key = match.group(1).strip()
        if citation_key_re.fullmatch(key):
            citation_references.append((key, path))

for key, path in citation_references:
    if key not in anchors:
        errors.append(
            f"unresolved citation anchor '{key}' referenced by {relative(path)}"
        )

mmd_sources = set((root / "figures" / "mermaid").glob("*.mmd"))
referenced_mmd = set()
for path in visited:
    if not path.exists() or path.suffix != ".adoc":
        continue
    text = path.read_text(encoding="utf-8")
    for match in image_re.finditer(text):
        raw = match.group(1).strip()
        if raw.endswith(".mmd"):
            referenced_mmd.add((path.parent / raw).resolve())

unused = sorted(
    p.relative_to(root) for p in mmd_sources if p.resolve() not in referenced_mmd
)
if unused:
    print("WARNING: unreferenced Mermaid sources:")
    for path in unused:
        print(f"  {path}")

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    f"Validated {len(visited)} AsciiDoc files, "
    f"{len(referenced_mmd)} Mermaid references, "
    f"{len(anchors)} explicit anchors, and "
    f"{len(citation_references)} citation references"
)
PY
}

render_diagrams() {
  local source output
  mkdir -p "$BUILD_DIR/figures/mermaid"

  # Python provides deterministic null-delimited sorting on both macOS and
  # Linux, avoiding the GNU-only `sort -z` dependency.
  while IFS= read -r -d '' source; do
    output="$BUILD_DIR/figures/mermaid/$(basename "${source%.mmd}.svg")"
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
}

prepare_sources() {
  cp "$ROOT/book.adoc" "$WORK_DIR/book.adoc"
  cp -R "$ROOT/chapters" "$WORK_DIR/chapters"
  cp -R "$ROOT/appendices" "$WORK_DIR/appendices"
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
    --attribute pdf-theme=default \
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

validate_references

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
  *)
    fail "Unknown build mode: $MODE"
    ;;
esac

printf 'Publication build completed: %s\n' "$MODE"
