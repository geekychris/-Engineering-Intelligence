#!/usr/bin/env python3
"""Render matplotlib data plots for the book into figures/plots/*.svg.

Deterministic (fixed seed); output styled with the cover palette so plots
sit naturally alongside chapter prose.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

NAVY = "#17365D"
DARK_NAVY = "#0E294D"
GOLD = "#B78331"
DEEP_GOLD = "#8A6224"
SEPIA = "#6C371F"
CREAM = "#F5EBD6"
SKY = "#8FC0E8"
RIVER = "#245A88"

FONT = {"family": "Georgia", "size": 11}


def _style_axes(ax):
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(NAVY)
        ax.spines[spine].set_linewidth(1.2)
    ax.tick_params(colors=NAVY, width=1.1)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily("Georgia")
    ax.title.set_color(NAVY)
    ax.xaxis.label.set_color(NAVY)
    ax.yaxis.label.set_color(NAVY)
    ax.grid(True, color=NAVY, alpha=0.08, linewidth=0.6)


def _figure(width_in=6.5, height_in=3.6):
    fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=120)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    return fig, ax


def cost_distribution(out: Path):
    rng = np.random.default_rng(20260716)
    samples = rng.lognormal(mean=np.log(2200), sigma=0.85, size=20000)
    p95 = np.quantile(samples, 0.95)
    samples_clipped = samples[samples <= p95 * 1.5]
    fig, ax = _figure()
    ax.hist(samples_clipped, bins=80, color=NAVY, alpha=0.78, edgecolor=CREAM, linewidth=0.4)
    median = np.median(samples)
    mean = np.mean(samples)
    ax.axvline(median, color=GOLD, linewidth=1.6, linestyle="--", label=f"Median ≈ ${median:,.0f}")
    ax.axvline(mean, color=SEPIA, linewidth=1.6, linestyle="-", label=f"Mean ≈ ${mean:,.0f}")
    ax.set_xlabel("Cost per Engineering Change (US$)", fontfamily="Georgia")
    ax.set_ylabel("Number of changes", fontfamily="Georgia")
    ax.set_title("Cost distribution is heavy-tailed: the mean is not the typical change",
                 fontfamily="Georgia", fontsize=11.5, pad=12)
    leg = ax.legend(frameon=False, prop={"family": "Georgia", "size": 10})
    for text in leg.get_texts():
        text.set_color(NAVY)
    _style_axes(ax)
    ax.set_xlim(0, p95 * 1.4)
    fig.tight_layout()
    fig.savefig(out, format="png", transparent=True, dpi=220)
    plt.close(fig)


def queueing_latency(out: Path):
    rho = np.linspace(0.05, 0.95, 400)
    service_time = 30.0  # minutes
    wait = service_time * rho / (1 - rho)
    fig, ax = _figure()
    ax.plot(rho, wait, color=NAVY, linewidth=2.4, label="Mean wait time W_q")
    ax.axvline(0.7, color=GOLD, linestyle="--", linewidth=1.4)
    ax.text(0.71, wait[np.argmin(np.abs(rho - 0.7))] + 15, "Sustainable\noperating point",
            color=GOLD, fontfamily="Georgia", fontsize=10)
    ax.axvline(0.9, color=SEPIA, linestyle="--", linewidth=1.4)
    ax.text(0.905, wait[np.argmin(np.abs(rho - 0.9))] + 30, "Wait explodes",
            color=SEPIA, fontfamily="Georgia", fontsize=10)
    ax.set_xlabel("Utilisation ρ of the constrained resource", fontfamily="Georgia")
    ax.set_ylabel("Expected queue wait (minutes)", fontfamily="Georgia")
    ax.set_title("Queueing delay grows non-linearly with utilisation",
                 fontfamily="Georgia", fontsize=11.5, pad=12)
    ax.set_ylim(0, 400)
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(out, format="png", transparent=True, dpi=220)
    plt.close(fig)


def context_switch_recovery(out: Path):
    t = np.linspace(0, 45, 400)
    productivity = 1 - 0.85 * np.exp(-t / 12)
    fig, ax = _figure()
    ax.plot(t, productivity, color=NAVY, linewidth=2.4)
    ax.fill_between(t, productivity, 1.0, color=GOLD, alpha=0.18, label="Attention debt")
    ax.axhline(1.0, color=NAVY, linewidth=0.9, linestyle=":", alpha=0.5)
    ax.text(28, 0.995, "Steady-state effectiveness",
            color=NAVY, fontfamily="Georgia", fontsize=9.5,
            va="bottom", ha="center")
    ax.set_xlabel("Minutes since interruption", fontfamily="Georgia")
    ax.set_ylabel("Fraction of pre-interruption effectiveness", fontfamily="Georgia")
    ax.set_title("Recovery after a context switch is gradual, not instant",
                 fontfamily="Georgia", fontsize=11.5, pad=12)
    ax.set_ylim(0, 1.05)
    leg = ax.legend(loc="lower right", frameon=False, prop={"family": "Georgia", "size": 10})
    for text in leg.get_texts():
        text.set_color(NAVY)
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(out, format="png", transparent=True, dpi=220)
    plt.close(fig)


def experiment_power(out: Path):
    # Power curves for several sample sizes (per arm) at α=0.05 two-sided,
    # detecting a proportional effect on a mean with known variance.
    effect = np.linspace(0.0, 0.25, 400)
    sigma = 1.0  # standardized outcome
    from math import erf, sqrt
    from statistics import NormalDist
    Z = NormalDist().inv_cdf(1 - 0.025)  # ~1.96
    fig, ax = _figure()
    colors = [SKY, RIVER, NAVY, DARK_NAVY]
    for color, n in zip(colors, (500, 2000, 8000, 32000)):
        se = sigma * np.sqrt(2.0 / n)
        power = 1 - np.array([NormalDist().cdf(Z - d / se) for d in effect]) \
                + np.array([NormalDist().cdf(-Z - d / se) for d in effect])
        ax.plot(effect * 100, power, color=color, linewidth=2.0,
                label=f"n = {n:,} per arm")
    ax.axhline(0.8, color=GOLD, linestyle="--", linewidth=1.4)
    ax.text(0.2, 0.82, "Conventional 80% power target",
            color=GOLD, fontfamily="Georgia", fontsize=10)
    ax.set_xlabel("Detectable effect size (% of baseline)", fontfamily="Georgia")
    ax.set_ylabel("Power to detect the effect", fontfamily="Georgia")
    ax.set_title("Minimum detectable effect shrinks with sample size, not with hope",
                 fontfamily="Georgia", fontsize=11.5, pad=12)
    ax.set_ylim(0, 1.05)
    leg = ax.legend(loc="lower right", frameon=False, prop={"family": "Georgia", "size": 10})
    for text in leg.get_texts():
        text.set_color(NAVY)
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(out, format="png", transparent=True, dpi=220)
    plt.close(fig)


def causal_dag(out: Path):
    fig, ax = plt.subplots(figsize=(6.5, 3.6), dpi=120)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    nodes = {
        "T": (2.0, 2.5, "AI reviewer\nadopted (T)"),
        "M": (5.0, 4.5, "Reviewer time\nallocated (M)"),
        "Y": (8.0, 2.5, "Change quality (Y)"),
        "U": (5.0, 0.9, "Team skill / repo maturity (U)"),
    }
    for _, (x, y, label) in nodes.items():
        ellipse = matplotlib.patches.FancyBboxPatch(
            (x - 1.0, y - 0.5), 2.0, 1.0,
            boxstyle="round,pad=0.02,rounding_size=0.35",
            linewidth=1.8, edgecolor=NAVY, facecolor=CREAM,
        )
        ax.add_patch(ellipse)
        ax.text(x, y, label, ha="center", va="center",
                fontfamily="Georgia", fontsize=11, color=NAVY)

    edges = [("T", "M", NAVY, "-"), ("M", "Y", NAVY, "-"),
             ("T", "Y", NAVY, "-"), ("U", "T", SEPIA, "--"),
             ("U", "Y", SEPIA, "--")]
    for src, dst, color, style in edges:
        x1, y1, _ = nodes[src]
        x2, y2, _ = nodes[dst]
        # trim to node edge
        dx, dy = x2 - x1, y2 - y1
        length = (dx ** 2 + dy ** 2) ** 0.5
        # start at ~1 unit from x1 (past the box), end at ~1 unit before x2
        margin = 1.05
        x1t, y1t = x1 + dx / length * margin, y1 + dy / length * margin
        x2t, y2t = x2 - dx / length * margin, y2 - dy / length * margin
        ax.annotate(
            "",
            xy=(x2t, y2t), xytext=(x1t, y1t),
            arrowprops=dict(arrowstyle="->", color=color, lw=1.6,
                            linestyle=style, shrinkA=0, shrinkB=0),
        )

    ax.text(5, 5.7, "Directed acyclic graph: paths, mediators, confounders",
            ha="center", fontfamily="Georgia", fontsize=11.5, color=NAVY)
    ax.text(5, 0.15,
            "Solid arrows: hypothesised causal paths. Dashed: confounding by U.",
            ha="center", fontfamily="Georgia", fontsize=9.5, color=SEPIA, style="italic")
    fig.tight_layout()
    fig.savefig(out, format="png", transparent=True, dpi=220)
    plt.close(fig)


PLOTS = {
    "cost-distribution.png": cost_distribution,
    "queueing-latency.png": queueing_latency,
    "context-switch-recovery.png": context_switch_recovery,
    "experiment-power.png": experiment_power,
    "causal-dag.png": causal_dag,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = "Georgia"
    plt.rcParams["svg.fonttype"] = "path"  # embed glyphs so prawn-svg is fine
    for name, fn in PLOTS.items():
        fn(args.output_dir / name)
    print(f"Rendered {len(PLOTS)} plots to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
