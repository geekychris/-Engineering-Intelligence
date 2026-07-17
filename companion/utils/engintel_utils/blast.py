"""Blast-radius scoring utilities (Ch 9)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .graph import DAG


@dataclass
class BlastRadiusScore:
    reach: float           # in [0, 1]
    exposure: float        # in [0, 1]
    reversibility: float   # in [0, 1], 1 = hardest to reverse

    def composite(self, w_reach: float = 0.4, w_exposure: float = 0.3,
                  w_reversibility: float = 0.3) -> float:
        return (w_reach * self.reach
                + w_exposure * self.exposure
                + w_reversibility * self.reversibility)


def blast_reach_from_dag(dag: DAG, changed_node: str,
                         customer_facing: set[str] | None = None) -> BlastRadiusScore:
    """Compute reach and exposure from an actual dependency DAG.

    - reach   = |descendants(changed)| / |services - {changed}|
    - exposure = |descendants ∩ customer_facing| / |customer_facing|
    - reversibility must be supplied separately (via `.with_reversibility`).
    """
    customer_facing = customer_facing or set()
    services = {n for n in dag.nodes if n != changed_node}
    reachable = dag.descendants(changed_node)
    reach = len(reachable) / max(1, len(services))
    exposure = (len(reachable & customer_facing) / max(1, len(customer_facing))
                if customer_facing else 0.0)
    return BlastRadiusScore(reach=reach, exposure=exposure, reversibility=0.0)


def apply_reversibility(score: BlastRadiusScore, reversibility: float) -> BlastRadiusScore:
    return BlastRadiusScore(
        reach=score.reach,
        exposure=score.exposure,
        reversibility=reversibility,
    )


def top_quartile(scores: Iterable[float], q: float = 0.75) -> float:
    import numpy as np
    return float(np.quantile(list(scores), q))
