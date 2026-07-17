#!/usr/bin/env python3
"""Render chapter-opening ornament plates.

The book cover establishes an illustrated identity but per-chapter unique
artwork requires an image model or human illustrator. As a portable
placeholder that still lifts the chapter openings visually, this script
produces a single decorative "compass rose" ornament band in the cover
palette; chapter files include it just before their first section.

If unique per-chapter illustrations are added later, drop them into
figures/plates/chapter-N.png and update the include in the chapter file.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, PathPatch
from matplotlib.path import Path as MplPath

NAVY = "#17365D"
DARK_NAVY = "#0E294D"
GOLD = "#B78331"
DEEP_GOLD = "#8A6224"
SEPIA = "#6C371F"
CREAM = "#EEE2C8"
PAPER = "#F5EBD6"


def _compass_rose(ax, cx, cy, radius, primary=GOLD, secondary=NAVY):
    outer_r = radius
    inner_r = radius * 0.35
    # Eight-pointed star
    verts = []
    codes = []
    for i in range(16):
        angle = math.pi / 8 * i - math.pi / 2
        r = outer_r if i % 4 == 0 else (inner_r if i % 2 == 0 else outer_r * 0.55)
        verts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        codes.append(MplPath.LINETO if verts else MplPath.MOVETO)
    codes[0] = MplPath.MOVETO
    verts.append(verts[0])
    codes.append(MplPath.CLOSEPOLY)
    star = PathPatch(MplPath(verts, codes), facecolor=primary,
                     edgecolor=secondary, linewidth=1.2, alpha=0.92)
    ax.add_patch(star)
    # Concentric ring
    ax.add_patch(Circle((cx, cy), outer_r * 1.15, fill=False,
                        edgecolor=secondary, linewidth=1.0))
    ax.add_patch(Circle((cx, cy), outer_r * 0.28, facecolor=CREAM,
                        edgecolor=secondary, linewidth=0.8))


def chapter_ornament(out: Path):
    # 6.5" x 0.9" band
    fig, ax = plt.subplots(figsize=(6.5, 0.9), dpi=240)
    fig.patch.set_alpha(0)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 15)
    ax.axis("off")
    ax.set_aspect("auto")

    # Top thick rule
    ax.plot([6, 94], [12.5, 12.5], color=NAVY, linewidth=1.8)
    # Bottom thin rule
    ax.plot([6, 94], [2.5, 2.5], color=NAVY, linewidth=0.7)

    # Central compass rose
    _compass_rose(ax, 50, 7.5, radius=3.6)

    # Ornamental brackets on either side of the rose
    for side_x in (32, 68):
        ax.plot([side_x - 4, side_x + 4], [7.5, 7.5],
                color=DEEP_GOLD, linewidth=0.9)
        ax.plot([side_x, side_x], [6, 9], color=DEEP_GOLD, linewidth=0.9)

    fig.tight_layout(pad=0)
    fig.savefig(out, format="png", transparent=True, dpi=240,
                bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = "Georgia"
    chapter_ornament(args.output_dir / "chapter-ornament.png")
    print(f"Rendered chapter ornament to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
