#!/usr/bin/env python3
"""Convert `# %%`-cell Python notebooks under companion/notebooks/ into
runnable Jupyter (.ipynb) files under companion/notebooks/ipynb/.

The .py files remain the canonical source (git-friendly, script-runnable);
the .ipynb files are regenerated from them so readers who prefer Jupyter
have zero setup friction.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

CELL_RE = re.compile(r"^# %%(?:\s+\[(\w+)\])?\s*$", re.MULTILINE)


def parse_cells(text: str) -> list[tuple[str, str]]:
    cells: list[tuple[str, str]] = []
    positions = [(m.start(), m.end(), m.group(1) or "code") for m in CELL_RE.finditer(text)]
    if not positions:
        return [("code", text)]
    prelude = text[: positions[0][0]]
    if prelude.strip():
        cells.append(("code", prelude.rstrip()))
    for i, (start, end, kind) in enumerate(positions):
        body_end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        body = text[end:body_end]
        # remove trailing whitespace
        body = body.strip("\n")
        if kind == "markdown":
            # Strip leading "# " from every line
            md_lines = []
            for line in body.split("\n"):
                if line.startswith("# "):
                    md_lines.append(line[2:])
                elif line.startswith("#"):
                    md_lines.append(line[1:].lstrip())
                else:
                    md_lines.append(line)
            body = "\n".join(md_lines).strip()
            cells.append(("markdown", body))
        else:
            cells.append(("code", body))
    return cells


def to_notebook(cells: list[tuple[str, str]]) -> dict:
    notebook_cells = []
    for kind, body in cells:
        if not body.strip():
            continue
        source_lines = body.splitlines(keepends=True)
        if source_lines and not source_lines[-1].endswith("\n"):
            source_lines[-1] += ""
        if kind == "markdown":
            notebook_cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": source_lines,
            })
        else:
            notebook_cells.append({
                "cell_type": "code",
                "metadata": {},
                "source": source_lines,
                "outputs": [],
                "execution_count": None,
            })
    return {
        "cells": notebook_cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    src_dir = root / "notebooks"
    out_dir = src_dir / "ipynb"
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for py in sorted(src_dir.glob("*.py")):
        text = py.read_text(encoding="utf-8")
        cells = parse_cells(text)
        nb = to_notebook(cells)
        out = out_dir / (py.stem + ".ipynb")
        out.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
        count += 1
    print(f"Wrote {count} notebooks to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
