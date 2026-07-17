#!/usr/bin/env python3
"""Validate the Engineering Intelligence AsciiDoc source tree.

This validator intentionally avoids Ruby, Node.js, and browser dependencies so it
can run as an early CI gate before the full HTML/PDF publication build.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


INCLUDE_RE = re.compile(r"include::([^\[]+)\[")
IMAGE_RE = re.compile(r"image::([^\[]+)\[")
ANCHOR_RE = re.compile(r"\[\[([^\],]+)(?:,[^\]]*)?\]\]")
XREF_RE = re.compile(r"<<([^,>]+)(?:,[^>]*)?>>")
CITATION_KEY_RE = re.compile(r"^[a-z][a-z0-9-]*\d{4}(?:-[a-z0-9-]+)?$")
CHAPTER_RE = re.compile(r"^(\d{2})-(.+)\.adoc$")
SOURCE_NOTES_RE = re.compile(r"^(\d{2})-(.+)-source-notes\.adoc$")
BOOK_CHAPTER_INCLUDE_RE = re.compile(
    r"include::chapters/([^\[]+\.adoc)\[leveloffset=\+(\d+)\]"
)


def validate(root: Path) -> int:
    root = root.resolve()
    book = root / "book.adoc"
    errors: list[str] = []
    warnings: list[str] = []
    visited: set[Path] = set()

    def relative(path: Path) -> str:
        try:
            return str(path.relative_to(root))
        except ValueError:
            return str(path)

    def walk(path: Path) -> None:
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

        for match in INCLUDE_RE.finditer(text):
            raw = match.group(1).strip()
            if "{" in raw or "}" in raw:
                warnings.append(
                    f"attribute-expanded include not statically resolved in "
                    f"{relative(path)}: {raw}"
                )
                continue
            walk((path.parent / raw).resolve())

        for match in IMAGE_RE.finditer(text):
            raw = match.group(1).strip()
            if raw.startswith(("http://", "https://", "data:")):
                continue
            if "{" in raw or "}" in raw:
                warnings.append(
                    f"attribute-expanded image not statically resolved in "
                    f"{relative(path)}: {raw}"
                )
                continue
            # Plot SVGs are generated during the build by scripts/render-plots.py
            # and land inside the jail. The generator's source list is
            # authoritative; skip these here.
            if raw.startswith("figures/plots/"):
                continue
            target = (path.parent / raw).resolve()
            if not target.exists():
                errors.append(
                    f"missing image source referenced by {relative(path)}: {raw}"
                )

    if not book.exists():
        print("ERROR: book.adoc was not found", file=sys.stderr)
        return 1

    walk(book)

    chapters_dir = root / "chapters"
    chapter_files: dict[str, Path] = {}
    source_note_files: dict[str, Path] = {}

    for path in sorted(chapters_dir.glob("*.adoc")):
        source_match = SOURCE_NOTES_RE.fullmatch(path.name)
        if source_match:
            source_note_files[source_match.group(1)] = path
            continue

        chapter_match = CHAPTER_RE.fullmatch(path.name)
        if chapter_match:
            chapter_files[chapter_match.group(1)] = path

    for number, chapter_path in sorted(chapter_files.items()):
        notes_path = source_note_files.get(number)
        if notes_path is None:
            errors.append(
                f"chapter {number} has no matching source-notes sidecar: "
                f"{relative(chapter_path)}"
            )
            continue

        expected_name = chapter_path.stem + "-source-notes.adoc"
        if notes_path.name != expected_name:
            errors.append(
                f"chapter {number} source-notes filename does not match chapter stem: "
                f"expected chapters/{expected_name}, found {relative(notes_path)}"
            )

    for number, notes_path in sorted(source_note_files.items()):
        if number not in chapter_files:
            errors.append(
                f"orphaned chapter source-notes sidecar: {relative(notes_path)}"
            )

    book_text = book.read_text(encoding="utf-8")
    chapter_includes = [
        (match.group(1), int(match.group(2)))
        for match in BOOK_CHAPTER_INCLUDE_RE.finditer(book_text)
    ]

    expected_include_sequence: list[tuple[str, int]] = []
    for number, chapter_path in sorted(chapter_files.items()):
        notes_path = source_note_files.get(number)
        expected_include_sequence.append((chapter_path.name, 1))
        if notes_path is not None:
            expected_include_sequence.append((notes_path.name, 2))

    if chapter_includes != expected_include_sequence:
        errors.append(
            "book.adoc chapter includes must list every chapter followed immediately "
            "by its matching source-notes sidecar, using leveloffset=+1 for chapters "
            "and leveloffset=+2 for source notes"
        )

    anchors: dict[str, Path] = {}
    citation_references: list[tuple[str, Path]] = []

    for path in sorted(visited):
        if not path.exists() or path.suffix != ".adoc":
            continue
        text = path.read_text(encoding="utf-8")

        for match in ANCHOR_RE.finditer(text):
            key = match.group(1).strip()
            if key in anchors:
                errors.append(
                    f"duplicate explicit anchor '{key}' in {relative(path)} and "
                    f"{relative(anchors[key])}"
                )
            else:
                anchors[key] = path

        for match in XREF_RE.finditer(text):
            key = match.group(1).strip()
            if CITATION_KEY_RE.fullmatch(key):
                citation_references.append((key, path))

    for key, path in citation_references:
        if key not in anchors:
            errors.append(
                f"unresolved citation anchor '{key}' referenced by {relative(path)}"
            )

    mermaid_dir = root / "figures" / "mermaid"
    mermaid_sources = set(mermaid_dir.glob("*.mmd")) if mermaid_dir.exists() else set()
    referenced_mermaid: set[Path] = set()

    for path in visited:
        if not path.exists() or path.suffix != ".adoc":
            continue
        text = path.read_text(encoding="utf-8")
        for match in IMAGE_RE.finditer(text):
            raw = match.group(1).strip()
            if raw.endswith(".mmd"):
                referenced_mermaid.add((path.parent / raw).resolve())

    unused = sorted(
        path.relative_to(root)
        for path in mermaid_sources
        if path.resolve() not in referenced_mermaid
    )
    for path in unused:
        warnings.append(f"unreferenced Mermaid source: {path}")

    for warning in sorted(set(warnings)):
        print(f"WARNING: {warning}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        "Validated "
        f"{len(visited)} AsciiDoc files, "
        f"{len(chapter_files)} chapter/source-note pairs, "
        f"{len(referenced_mermaid)} Mermaid references, "
        f"{len(anchors)} explicit anchors, and "
        f"{len(citation_references)} citation references"
    )
    return 0


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    return validate(root)


if __name__ == "__main__":
    raise SystemExit(main())
