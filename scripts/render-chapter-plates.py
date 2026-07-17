#!/usr/bin/env python3
"""Render chapter-opening ornament plates.

Produces a decorative rule with a central topic badge for each chapter
theme. The badge varies (compass, magnifying glass, balance, profile,
gears, cycle) but the surrounding rule stays constant, so the book
opens each chapter with a consistent visual anchor while still hinting
at the chapter's subject.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, PathPatch, Rectangle
from matplotlib.path import Path as MplPath

NAVY = "#17365D"
DARK_NAVY = "#0E294D"
GOLD = "#B78331"
DEEP_GOLD = "#8A6224"
SEPIA = "#6C371F"
CREAM = "#EEE2C8"
PAPER = "#F5EBD6"


# ---- Badge drawings (each draws at (cx,cy) within a ~6 unit radius) ----

def _badge_frame(ax, cx, cy, radius):
    ax.add_patch(Circle((cx, cy), radius * 1.15, fill=False,
                        edgecolor=NAVY, linewidth=1.0))


def compass(ax, cx, cy, r):
    verts = []
    codes = []
    for i in range(16):
        angle = math.pi / 8 * i - math.pi / 2
        rr = r if i % 4 == 0 else (r * 0.35 if i % 2 == 0 else r * 0.55)
        verts.append((cx + rr * math.cos(angle), cy + rr * math.sin(angle)))
        codes.append(MplPath.LINETO)
    codes[0] = MplPath.MOVETO
    verts.append(verts[0]); codes.append(MplPath.CLOSEPOLY)
    ax.add_patch(PathPatch(MplPath(verts, codes),
                           facecolor=GOLD, edgecolor=NAVY, linewidth=1.1))
    ax.add_patch(Circle((cx, cy), r * 0.28, facecolor=CREAM,
                        edgecolor=NAVY, linewidth=0.8))
    _badge_frame(ax, cx, cy, r)


def magnifier(ax, cx, cy, r):
    lens_cx, lens_cy = cx - r * 0.15, cy + r * 0.15
    lens_r = r * 0.7
    ax.add_patch(Circle((lens_cx, lens_cy), lens_r, fill=False,
                        edgecolor=NAVY, linewidth=1.6))
    ax.add_patch(Circle((lens_cx, lens_cy), lens_r * 0.85, facecolor=GOLD,
                        alpha=0.35, edgecolor="none"))
    # handle
    handle_start = (lens_cx + lens_r * 0.7, lens_cy - lens_r * 0.7)
    handle_end = (cx + r * 0.85, cy - r * 0.85)
    ax.plot([handle_start[0], handle_end[0]],
            [handle_start[1], handle_end[1]],
            color=NAVY, linewidth=2.2, solid_capstyle="round")
    _badge_frame(ax, cx, cy, r)


def balance(ax, cx, cy, r):
    # central beam
    ax.plot([cx - r * 0.8, cx + r * 0.8], [cy + r * 0.2, cy + r * 0.2],
            color=NAVY, linewidth=1.6)
    # vertical stand
    ax.plot([cx, cx], [cy - r * 0.7, cy + r * 0.2], color=NAVY, linewidth=1.6)
    # base
    ax.plot([cx - r * 0.5, cx + r * 0.5], [cy - r * 0.7, cy - r * 0.7],
            color=NAVY, linewidth=1.6)
    # pans (semi-circles)
    for sign in (-1, 1):
        px = cx + sign * r * 0.75
        py = cy - r * 0.05
        pan_verts = [
            (px - r * 0.35, py),
            (px - r * 0.35, py - r * 0.25),
            (px + r * 0.35, py - r * 0.25),
            (px + r * 0.35, py),
        ]
        ax.add_patch(PathPatch(
            MplPath(pan_verts, [MplPath.MOVETO, MplPath.LINETO,
                                 MplPath.LINETO, MplPath.LINETO]),
            fill=True, facecolor=GOLD, edgecolor=NAVY, linewidth=1.1))
        # hanger
        ax.plot([px, px], [py, cy + r * 0.2], color=NAVY, linewidth=1.0)
    _badge_frame(ax, cx, cy, r)


def profile(ax, cx, cy, r):
    # simplified profile: head + shoulders silhouette in cream on navy
    head_verts = [
        (cx, cy + r * 0.9),
        (cx + r * 0.45, cy + r * 0.6),
        (cx + r * 0.42, cy + r * 0.15),
        (cx + r * 0.55, cy - r * 0.05),
        (cx + r * 0.85, cy - r * 0.7),
        (cx - r * 0.85, cy - r * 0.7),
        (cx - r * 0.55, cy - r * 0.05),
        (cx - r * 0.42, cy + r * 0.15),
        (cx - r * 0.45, cy + r * 0.6),
        (cx, cy + r * 0.9),
    ]
    ax.add_patch(PathPatch(MplPath(head_verts),
                           facecolor=NAVY, edgecolor=NAVY, linewidth=0.8))
    # small gold spark to suggest cognition
    ax.add_patch(Circle((cx, cy + r * 0.35), r * 0.11,
                        facecolor=GOLD, edgecolor=DEEP_GOLD, linewidth=0.6))
    _badge_frame(ax, cx, cy, r)


def gears(ax, cx, cy, r):
    def _gear(cx0, cy0, radius, teeth=10, tooth_h=0.22):
        verts = []
        codes = []
        for i in range(teeth * 2):
            angle = 2 * math.pi * i / (teeth * 2)
            rr = radius * (1 + tooth_h) if i % 2 == 0 else radius
            verts.append((cx0 + rr * math.cos(angle),
                          cy0 + rr * math.sin(angle)))
            codes.append(MplPath.LINETO)
        codes[0] = MplPath.MOVETO
        verts.append(verts[0]); codes.append(MplPath.CLOSEPOLY)
        ax.add_patch(PathPatch(MplPath(verts, codes),
                               facecolor=GOLD, edgecolor=NAVY, linewidth=1.0))
        ax.add_patch(Circle((cx0, cy0), radius * 0.32, facecolor=CREAM,
                            edgecolor=NAVY, linewidth=0.7))

    _gear(cx - r * 0.4, cy + r * 0.15, r * 0.6)
    _gear(cx + r * 0.45, cy - r * 0.25, r * 0.45)
    _badge_frame(ax, cx, cy, r)


def cycle(ax, cx, cy, r):
    # circular arrow suggesting a learning loop
    theta = 0
    arc_r = r * 0.8
    verts = []
    codes = []
    steps = 60
    start = math.radians(30)
    end = math.radians(330)
    for i in range(steps + 1):
        t = start + (end - start) * i / steps
        verts.append((cx + arc_r * math.cos(t), cy + arc_r * math.sin(t)))
        codes.append(MplPath.LINETO if i else MplPath.MOVETO)
    ax.add_patch(PathPatch(MplPath(verts, codes), fill=False,
                           edgecolor=NAVY, linewidth=2.0))
    # arrowhead at the end
    tx, ty = verts[-1]
    ax.annotate("", xy=(tx + arc_r * 0.05, ty - arc_r * 0.05),
                xytext=(tx, ty),
                arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=2))
    # central gold dot
    ax.add_patch(Circle((cx, cy), r * 0.22, facecolor=GOLD,
                        edgecolor=NAVY, linewidth=0.9))
    _badge_frame(ax, cx, cy, r)


BADGES = {
    "compass": compass,
    "magnifier": magnifier,
    "balance": balance,
    "profile": profile,
    "gears": gears,
    "cycle": cycle,
}


# ---- Ornament plate composition ----

def render_plate(out: Path, badge: str) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 0.9), dpi=240)
    fig.patch.set_alpha(0)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 15)
    ax.axis("off")
    ax.set_aspect("auto")

    ax.plot([6, 94], [12.5, 12.5], color=NAVY, linewidth=1.8)
    ax.plot([6, 94], [2.5, 2.5], color=NAVY, linewidth=0.7)
    for side_x in (32, 68):
        ax.plot([side_x - 4, side_x + 4], [7.5, 7.5],
                color=DEEP_GOLD, linewidth=0.9)
        ax.plot([side_x, side_x], [6, 9], color=DEEP_GOLD, linewidth=0.9)

    BADGES[badge](ax, 50, 7.5, 3.6)

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
    # Default (used when no chapter mapping matches).
    render_plate(args.output_dir / "chapter-ornament.png", "compass")
    for badge in BADGES:
        render_plate(args.output_dir / f"chapter-ornament-{badge}.png", badge)
    print(f"Rendered {1 + len(BADGES)} chapter ornaments to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
