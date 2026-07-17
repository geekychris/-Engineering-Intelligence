"""Dependency-graph tools used by blast-radius and critical-path notebooks."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class DAG:
    """Tiny DAG implementation. Nodes are strings; edges are (u, v) tuples."""
    nodes: set[str] = field(default_factory=set)
    edges: set[tuple[str, str]] = field(default_factory=set)

    def add_node(self, u: str) -> None:
        self.nodes.add(u)

    def add_edge(self, u: str, v: str) -> None:
        self.nodes.add(u)
        self.nodes.add(v)
        self.edges.add((u, v))

    def successors(self, u: str) -> list[str]:
        return [b for (a, b) in self.edges if a == u]

    def predecessors(self, v: str) -> list[str]:
        return [a for (a, b) in self.edges if b == v]

    def descendants(self, u: str) -> set[str]:
        """All nodes reachable from `u`."""
        seen: set[str] = set()
        q = deque([u])
        while q:
            x = q.popleft()
            for y in self.successors(x):
                if y not in seen:
                    seen.add(y)
                    q.append(y)
        return seen

    def ancestors(self, v: str) -> set[str]:
        seen: set[str] = set()
        q = deque([v])
        while q:
            x = q.popleft()
            for y in self.predecessors(x):
                if y not in seen:
                    seen.add(y)
                    q.append(y)
        return seen

    def topological_order(self) -> list[str]:
        indeg: dict[str, int] = {n: 0 for n in self.nodes}
        for (_, v) in self.edges:
            indeg[v] += 1
        ready = deque([n for n, d in indeg.items() if d == 0])
        order: list[str] = []
        while ready:
            u = ready.popleft()
            order.append(u)
            for v in self.successors(u):
                indeg[v] -= 1
                if indeg[v] == 0:
                    ready.append(v)
        if len(order) != len(self.nodes):
            raise ValueError("graph contains a cycle")
        return order


def critical_path(g: DAG, duration: dict[str, float]) -> tuple[list[str], float]:
    """Longest-duration path through a DAG whose nodes carry a duration."""
    order = g.topological_order()
    best_to: dict[str, float] = {n: duration.get(n, 0.0) for n in g.nodes}
    parent: dict[str, str | None] = {n: None for n in g.nodes}
    for u in order:
        for v in g.successors(u):
            candidate = best_to[u] + duration.get(v, 0.0)
            if candidate > best_to[v]:
                best_to[v] = candidate
                parent[v] = u
    # find sink with highest best_to
    end = max(g.nodes, key=lambda n: best_to[n])
    path = []
    cur: str | None = end
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path, best_to[end]


def parallelism_ratio(g: DAG, duration: dict[str, float]) -> float:
    """Total work divided by critical-path length."""
    total = sum(duration.get(n, 0.0) for n in g.nodes)
    _, cp = critical_path(g, duration)
    if cp == 0:
        return 0.0
    return total / cp
