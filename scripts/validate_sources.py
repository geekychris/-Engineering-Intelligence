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
            target = (path.parent / raw).resolve()
            if not target.exists():
                errors.append(
                    f"missing image source referenced by {relative(path)}: {raw}"
                )

    if not book.exists():
        print("ERROR: book.adoc was not found", file=sys.stderr)
        return 1

    walk(book)

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
