"""Monte Carlo simulation helpers for engineering-cost analysis."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np


@dataclass
class CostDistribution:
    """A named cost distribution with a sampler and diagnostics."""
    name: str
    sampler: Callable[[np.random.Generator, int], np.ndarray]

    def sample(self, n: int, seed: int = 0) -> np.ndarray:
        rng = np.random.default_rng(seed)
        return self.sampler(rng, n)


def lognormal(mean_of_log: float, sigma_of_log: float, *, name: str = "cost") -> CostDistribution:
    return CostDistribution(
        name=name,
        sampler=lambda rng, n: rng.lognormal(mean=mean_of_log, sigma=sigma_of_log, size=n),
    )


def triangular(lo: float, mode: float, hi: float, *, name: str = "cost") -> CostDistribution:
    return CostDistribution(
        name=name,
        sampler=lambda rng, n: rng.triangular(lo, mode, hi, size=n),
    )


def sum_cost(distributions: Sequence[CostDistribution], n: int = 20_000,
             seed: int = 0) -> dict[str, float]:
    """Monte Carlo estimate of the summed cost across independent components."""
    rng = np.random.default_rng(seed)
    total = np.zeros(n, dtype=float)
    for d in distributions:
        total += d.sampler(rng, n)
    return {
        "mean": float(total.mean()),
        "median": float(np.median(total)),
        "p90": float(np.quantile(total, 0.90)),
        "p95": float(np.quantile(total, 0.95)),
        "p99": float(np.quantile(total, 0.99)),
    }


def sensitivity_scan(baseline: dict[str, float],
                     scenarios: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    """Compute delta from baseline for a set of named scenarios."""
    out: dict[str, dict[str, float]] = {}
    for name, override in scenarios.items():
        scenario = dict(baseline)
        scenario.update(override)
        out[name] = {k: scenario[k] - baseline[k] for k in scenario if k in baseline}
    return out
