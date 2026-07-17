"""Statistical utilities used across the companion notebooks."""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import NormalDist
from typing import Iterable, Sequence

import numpy as np


@dataclass
class Interval:
    """A named interval with lower, upper, and level."""
    lower: float
    upper: float
    level: float = 0.95

    def contains(self, x: float) -> bool:
        return self.lower <= x <= self.upper

    def __repr__(self) -> str:
        pct = int(self.level * 100)
        return f"{pct}% [{self.lower:.4g}, {self.upper:.4g}]"


def bootstrap_mean_ci(samples: Sequence[float], *,
                      n_boot: int = 5000, level: float = 0.95,
                      seed: int = 0) -> Interval:
    """Percentile bootstrap CI for the sample mean.

    Suitable for skewed or heavy-tailed engineering distributions where the
    normal-CLT interval understates uncertainty in the mean.
    """
    rng = np.random.default_rng(seed)
    arr = np.asarray(samples, dtype=float)
    n = len(arr)
    if n < 2:
        raise ValueError("need at least two samples")
    idx = rng.integers(0, n, size=(n_boot, n))
    means = arr[idx].mean(axis=1)
    lo = float(np.quantile(means, (1 - level) / 2))
    hi = float(np.quantile(means, 1 - (1 - level) / 2))
    return Interval(lower=lo, upper=hi, level=level)


def bootstrap_median_ci(samples: Sequence[float], *,
                        n_boot: int = 5000, level: float = 0.95,
                        seed: int = 0) -> Interval:
    """Percentile bootstrap CI for the sample median."""
    rng = np.random.default_rng(seed)
    arr = np.asarray(samples, dtype=float)
    n = len(arr)
    idx = rng.integers(0, n, size=(n_boot, n))
    medians = np.median(arr[idx], axis=1)
    lo = float(np.quantile(medians, (1 - level) / 2))
    hi = float(np.quantile(medians, 1 - (1 - level) / 2))
    return Interval(lower=lo, upper=hi, level=level)


def two_sample_z(y_treat: Sequence[float], y_ctrl: Sequence[float],
                 *, level: float = 0.95) -> tuple[float, Interval]:
    """Two-sample z estimate of the mean difference y_treat - y_ctrl."""
    t = np.asarray(y_treat, dtype=float)
    c = np.asarray(y_ctrl, dtype=float)
    diff = t.mean() - c.mean()
    se = sqrt(t.var(ddof=1) / len(t) + c.var(ddof=1) / len(c))
    z = NormalDist().inv_cdf(1 - (1 - level) / 2)
    return float(diff), Interval(lower=float(diff - z * se),
                                 upper=float(diff + z * se), level=level)


def sample_size_two_arm(sigma: float, mde: float, *,
                        alpha: float = 0.05, power: float = 0.80) -> int:
    """Required per-arm sample size for a two-sided z-test."""
    z_alpha = NormalDist().inv_cdf(1 - alpha / 2)
    z_beta = NormalDist().inv_cdf(power)
    n = 2 * ((z_alpha + z_beta) * sigma / mde) ** 2
    return int(np.ceil(n))


def power_curve(effects: Sequence[float], n_per_arm: int, sigma: float,
                *, alpha: float = 0.05) -> np.ndarray:
    """Power for a two-sided z-test given effect sizes, n, and outcome sigma."""
    se = sigma * sqrt(2.0 / n_per_arm)
    z = NormalDist().inv_cdf(1 - alpha / 2)
    upper = np.array([NormalDist().cdf(z - d / se) for d in effects])
    lower = np.array([NormalDist().cdf(-z - d / se) for d in effects])
    return 1.0 - upper + lower


def obrien_fleming_boundary(k: int, alpha: float = 0.05) -> np.ndarray:
    """O'Brien-Fleming group-sequential critical z-values at k evenly spaced looks."""
    if k < 1:
        raise ValueError("need at least one look")
    K = k
    boundaries = np.array([
        NormalDist().inv_cdf(1 - alpha / (2 * K)) * sqrt(K / (i + 1))
        for i in range(K)
    ])
    return boundaries


def beta_binomial_posterior(successes: int, trials: int,
                            *, alpha_prior: float = 1.0,
                            beta_prior: float = 1.0,
                            level: float = 0.95) -> tuple[float, Interval]:
    """Posterior mean and credible interval for a Beta-Binomial rate."""
    from scipy.stats import beta as beta_dist
    a = alpha_prior + successes
    b = beta_prior + (trials - successes)
    mean = a / (a + b)
    lo = float(beta_dist.ppf((1 - level) / 2, a, b))
    hi = float(beta_dist.ppf(1 - (1 - level) / 2, a, b))
    return float(mean), Interval(lower=lo, upper=hi, level=level)
