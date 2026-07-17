"""Toy Engineering Change reconstruction from event streams.

This is a simplified reference implementation. It intentionally trades
completeness for readability so a reader can follow the shape of the
reconstruction described in Chapter 3.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class Event:
    at: int
    event: str
    payload: dict


@dataclass
class EngineeringChange:
    id: str
    author_id: str
    pr_ids: list[str] = field(default_factory=list)
    opened_at: int = 0
    confidence: float = 1.0
    linkage: str = "deterministic"   # or "probabilistic"

    def as_dict(self) -> dict:
        return {
            "engineering_change_id": self.id,
            "author_id": self.author_id,
            "pr_ids": self.pr_ids,
            "opened_at": self.opened_at,
            "reconstruction_confidence": round(self.confidence, 3),
            "linkage_method": self.linkage,
        }


def load_jsonl(path: str | Path) -> list[dict]:
    """Read a JSON Lines file into a list of dicts."""
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def reconstruct_changes(pr_events: Iterable[dict],
                        *,
                        temporal_window_seconds: int = 86_400,
                        probabilistic_penalty: float = 0.08,
                        min_confidence: float = 0.55) -> list[EngineeringChange]:
    """Group pull-request events into Engineering Changes.

    Rules — deliberately simple:

    - Group by author.
    - Within an author, PRs opened within `temporal_window_seconds` of each
      other are candidate members of one Engineering Change.
    - A single-PR group is deterministic (confidence 1.0).
    - Multi-PR groups are probabilistic (confidence decreases with member
      count).

    Returns a list of `EngineeringChange` in stable order.
    """
    opened = [e for e in pr_events if e.get("event") == "pull_request.opened"]
    opened.sort(key=lambda e: (e["author_id"], e["at"]))

    changes: list[EngineeringChange] = []
    ec_num = 0
    by_author: dict[str, list[dict]] = defaultdict(list)
    for e in opened:
        by_author[e["author_id"]].append(e)

    for author, events in by_author.items():
        # walk events in time order, opening a new group when the temporal gap
        # exceeds `temporal_window_seconds`.
        current: list[dict] = []
        for e in events:
            if not current or (e["at"] - current[-1]["at"]) <= temporal_window_seconds:
                current.append(e)
            else:
                _flush(current, changes, author)
                current = [e]
        if current:
            _flush(current, changes, author)

    # apply probabilistic penalty
    for c in changes:
        if len(c.pr_ids) > 1:
            c.linkage = "probabilistic"
            c.confidence = max(min_confidence,
                                1.0 - probabilistic_penalty * (len(c.pr_ids) - 1))
        else:
            c.linkage = "deterministic"
            c.confidence = 1.0

    return changes


def _flush(events: list[dict], changes: list[EngineeringChange], author: str) -> None:
    idx = len(changes) + 1
    changes.append(EngineeringChange(
        id=f"ec_{idx:06d}",
        author_id=author,
        pr_ids=[e["pr_id"] for e in events],
        opened_at=min(e["at"] for e in events),
    ))


def reconstruction_summary(changes: list[EngineeringChange]) -> dict[str, float]:
    """Aggregate diagnostics for a reconstructed change list."""
    total = len(changes)
    if total == 0:
        return {"total": 0}
    multi = sum(1 for c in changes if len(c.pr_ids) > 1)
    mean_conf = sum(c.confidence for c in changes) / total
    low_conf = sum(1 for c in changes if c.confidence < 0.80)
    return {
        "total": total,
        "single_pr": total - multi,
        "multi_pr": multi,
        "mean_confidence": round(mean_conf, 3),
        "below_confidence_0.80": low_conf,
    }
