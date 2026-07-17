"""Metric specification, versioning, and composite metric helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Sequence

import numpy as np


@dataclass
class MetricSpec:
    """Small metric-specification object mirroring Appendix B fields."""
    identifier: str
    title: str
    version: str
    construct: str
    decision: str
    unit_of_analysis: str
    formula: str
    guardrails: list[str] = field(default_factory=list)
    owner: str = ""
    notes: str = ""

    def bump(self, kind: str, reason: str) -> "MetricSpec":
        """Return a new spec with an incremented semantic version.

        `kind` ∈ {'patch', 'minor', 'major'}.
        """
        maj, min_, pat = (int(p) for p in self.version.split("."))
        if kind == "patch":
            pat += 1
        elif kind == "minor":
            min_ += 1
            pat = 0
        elif kind == "major":
            maj += 1
            min_ = 0
            pat = 0
        else:
            raise ValueError(f"unknown bump kind: {kind}")
        return MetricSpec(
            identifier=self.identifier,
            title=self.title,
            version=f"{maj}.{min_}.{pat}",
            construct=self.construct,
            decision=self.decision,
            unit_of_analysis=self.unit_of_analysis,
            formula=self.formula,
            guardrails=list(self.guardrails),
            owner=self.owner,
            notes=(self.notes + "\n" if self.notes else "") + f"v{maj}.{min_}.{pat}: {reason}",
        )


@dataclass
class CompositeMetric:
    """Weighted composite index over standardized components (Ch 5)."""
    name: str
    components: dict[str, Callable[[dict], float]]
    weights: dict[str, float]

    def score_one(self, row: dict) -> float:
        return sum(self.weights[k] * fn(row) for k, fn in self.components.items())

    def score_many(self, rows: Sequence[dict]) -> np.ndarray:
        return np.asarray([self.score_one(r) for r in rows])


def zscore(values: Sequence[float]) -> np.ndarray:
    """Standardise a sequence of values to mean 0, std 1."""
    arr = np.asarray(values, dtype=float)
    mu = arr.mean()
    sigma = arr.std(ddof=1)
    if sigma == 0:
        return arr - mu
    return (arr - mu) / sigma


def compare_metric_versions(
    values_v1: Sequence[float],
    values_v2: Sequence[float],
) -> dict[str, float]:
    """Diagnostics for the difference between two metric-version series."""
    v1 = np.asarray(values_v1, dtype=float)
    v2 = np.asarray(values_v2, dtype=float)
    if len(v1) != len(v2):
        raise ValueError("versions must cover matching populations")
    delta = v2 - v1
    return {
        "n": len(v1),
        "mean_delta": float(delta.mean()),
        "median_delta": float(np.median(delta)),
        "max_absolute_delta": float(np.abs(delta).max()),
        "correlation": float(np.corrcoef(v1, v2)[0, 1]),
    }
