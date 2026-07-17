"""Deterministic synthetic engineering-telemetry generator."""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

SECONDS_PER_DAY = 86_400
EPOCH_START = 1_734_566_400  # 2026-01-01T00:00:00Z, fixed for reproducibility

FIRST_NAMES = [
    "Alex", "Blair", "Casey", "Dana", "Emerson", "Fran", "Gale", "Harper",
    "Indie", "Jules", "Kai", "Lane", "Morgan", "Noor", "Ollie", "Parker",
    "Quinn", "Reese", "Sage", "Toni", "Uma", "Val", "Wren", "Xin",
    "Yael", "Zev",
]
LAST_NAMES = [
    "Adler", "Baird", "Chen", "Delgado", "Eriksen", "Faruq", "Garvey",
    "Halim", "Iyengar", "Jorgensen", "Kobayashi", "Lombardi", "Miura",
    "Nakamura", "Ogilvy", "Popescu", "Qureshi", "Rahim", "Sato",
    "Tanaka", "Ustinov", "Villanueva", "Watanabe", "Xie", "Yamamoto",
    "Zheng",
]
TEAM_NAMES = [
    "Aurora", "Beacon", "Cinder", "Delta", "Ember", "Fjord", "Glacier",
    "Halcyon", "Ibis", "Juniper", "Kestrel", "Lyric", "Meridian", "Nimbus",
    "Onyx", "Prism", "Quartz", "Ridge", "Solstice", "Terra", "Umbra",
    "Vega", "Willow", "Xenon", "Yarrow", "Zephyr",
]
DOMAINS = [
    "payments", "identity", "search", "notifications", "growth", "billing",
    "accounts", "checkout", "risk", "content", "logging", "reliability",
    "infra", "data-platform", "ml-platform", "ai-review",
]
LIFECYCLE_STATES = [
    "opened", "review_requested", "review_submitted", "comment",
    "changes_requested", "merged", "closed", "reopened",
]


@dataclass
class Config:
    days: int = 30
    teams: int = 20
    seed: int = 42
    engineers_per_team_mean: float = 6.0
    services_per_team_mean: float = 3.0
    pr_per_engineer_per_day_mean: float = 1.1
    review_specialists_fraction: float = 0.06
    ai_review_adoption_after_day: int = 15
    incident_rate_per_100_deploys: float = 3.5


@dataclass
class _Actor:
    id: str
    kind: str          # human, bot, agent
    display_name: str
    team_id: str
    role: str          # engineer, reviewer, specialist, sre, agent
    scarcity: float    # 1.0 = plentiful; 2.5+ = specialist


@dataclass
class _Team:
    id: str
    name: str
    domain: str


@dataclass
class _Service:
    id: str
    team_id: str
    name: str
    fanout: int         # rough dependency count
    customer_facing: bool


class Generator:
    """Deterministic synthetic telemetry generator."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.rng = random.Random(config.seed)

    # ---- Populations ----

    def _make_teams(self) -> list[_Team]:
        picked = self.rng.sample(range(len(TEAM_NAMES)), self.config.teams)
        teams: list[_Team] = []
        for i, idx in enumerate(picked):
            domain = self.rng.choice(DOMAINS)
            teams.append(_Team(id=f"team_{i+1:03d}", name=TEAM_NAMES[idx], domain=domain))
        return teams

    def _make_actors(self, teams: list[_Team]) -> list[_Actor]:
        actors: list[_Actor] = []
        n = 1
        for team in teams:
            engineers_count = max(2, int(self.rng.gauss(self.config.engineers_per_team_mean, 1.4)))
            for _ in range(engineers_count):
                first = self.rng.choice(FIRST_NAMES)
                last = self.rng.choice(LAST_NAMES)
                # Some engineers are specialists (scarce reviewer capacity).
                is_specialist = self.rng.random() < self.config.review_specialists_fraction
                role = "specialist" if is_specialist else "engineer"
                scarcity = self.rng.uniform(2.4, 3.5) if is_specialist else self.rng.uniform(0.9, 1.3)
                actors.append(_Actor(
                    id=f"actor_{n:05d}",
                    kind="human",
                    display_name=f"{first} {last}",
                    team_id=team.id,
                    role=role,
                    scarcity=round(scarcity, 2),
                ))
                n += 1
            # Add one bot per team.
            actors.append(_Actor(
                id=f"actor_{n:05d}",
                kind="bot",
                display_name=f"ci-{team.name.lower()}-bot",
                team_id=team.id,
                role="ci-bot",
                scarcity=1.0,
            ))
            n += 1
        # Add a few AI agents that appear across teams.
        for _ in range(3):
            actors.append(_Actor(
                id=f"actor_{n:05d}",
                kind="agent",
                display_name=f"ai-review-agent-{n}",
                team_id=teams[self.rng.randrange(len(teams))].id,
                role="agent",
                scarcity=1.0,
            ))
            n += 1
        return actors

    def _make_services(self, teams: list[_Team]) -> list[_Service]:
        services: list[_Service] = []
        n = 1
        for team in teams:
            count = max(1, int(self.rng.gauss(self.config.services_per_team_mean, 1.2)))
            for j in range(count):
                services.append(_Service(
                    id=f"svc_{n:04d}",
                    team_id=team.id,
                    name=f"{team.name.lower()}-{j+1}",
                    fanout=self.rng.randint(0, 12),
                    customer_facing=self.rng.random() < 0.20,
                ))
                n += 1
        return services

    # ---- Event streams ----

    def _emit_prs(self, actors: list[_Actor], services: list[_Service]) -> Iterator[dict]:
        engineers = [a for a in actors if a.kind == "human" and a.role == "engineer"]
        reviewers = [a for a in actors if a.kind == "human"]
        pr_num = 1
        for day in range(self.config.days):
            day_start = EPOCH_START + day * SECONDS_PER_DAY
            for author in engineers:
                lam = self.config.pr_per_engineer_per_day_mean
                # Poisson-shaped PR count for this engineer/day.
                k = _poisson(self.rng, lam)
                for _ in range(k):
                    service = self.rng.choice(services)
                    open_offset = self.rng.randint(9 * 3600, 17 * 3600)
                    opened_at = day_start + open_offset
                    review_lag = int(self.rng.gauss(4.9 * 3600, 3.2 * 3600))
                    review_lag = max(600, review_lag)  # >= 10 min
                    review_at = opened_at + review_lag

                    merged = self.rng.random() < 0.86
                    resolution_lag = int(self.rng.gauss(6.2 * 3600, 5.0 * 3600))
                    resolution_lag = max(1200, resolution_lag)
                    resolved_at = review_at + resolution_lag
                    reviewer = self.rng.choice([r for r in reviewers if r.id != author.id])

                    pr_id = f"pr_{pr_num:06d}"
                    yield {
                        "event": "pull_request.opened",
                        "at": opened_at,
                        "pr_id": pr_id,
                        "author_id": author.id,
                        "service_id": service.id,
                        "team_id": author.team_id,
                    }
                    yield {
                        "event": "pull_request.review_requested",
                        "at": opened_at + 300,
                        "pr_id": pr_id,
                        "reviewer_id": reviewer.id,
                    }
                    yield {
                        "event": "pull_request.review_submitted",
                        "at": review_at,
                        "pr_id": pr_id,
                        "reviewer_id": reviewer.id,
                        "state": "approved" if merged else "changes_requested",
                    }
                    yield {
                        "event": "pull_request.merged" if merged else "pull_request.closed",
                        "at": resolved_at,
                        "pr_id": pr_id,
                    }
                    pr_num += 1

    def _emit_ci_runs(self, pr_events: list[dict]) -> Iterator[dict]:
        opened = [e for e in pr_events if e["event"] == "pull_request.opened"]
        run_num = 1
        for pr in opened:
            # 1-3 CI runs per PR
            runs = self.rng.randint(1, 3)
            for i in range(runs):
                started_at = pr["at"] + i * self.rng.randint(1200, 4800)
                duration = int(self.rng.gauss(720, 240))
                duration = max(120, duration)
                passed = self.rng.random() < 0.83
                yield {
                    "event": "ci.run.started",
                    "at": started_at,
                    "run_id": f"ci_{run_num:07d}",
                    "pr_id": pr["pr_id"],
                }
                yield {
                    "event": "ci.run.finished",
                    "at": started_at + duration,
                    "run_id": f"ci_{run_num:07d}",
                    "pr_id": pr["pr_id"],
                    "outcome": "passed" if passed else "failed",
                }
                run_num += 1

    def _emit_deployments(self, pr_events: list[dict], services: list[_Service]) -> Iterator[dict]:
        merged = [e for e in pr_events if e["event"] == "pull_request.merged"]
        # Attach service_id to each merged PR by looking back at opened events.
        opened_by_id = {e["pr_id"]: e for e in pr_events if e["event"] == "pull_request.opened"}
        dep_num = 1
        for pr in merged:
            svc_id = opened_by_id[pr["pr_id"]]["service_id"]
            lag = int(self.rng.gauss(2.4 * 3600, 1.4 * 3600))
            lag = max(600, lag)
            yield {
                "event": "deployment.started",
                "at": pr["at"] + lag,
                "deployment_id": f"dep_{dep_num:07d}",
                "pr_id": pr["pr_id"],
                "service_id": svc_id,
                "environment": "production",
            }
            duration = int(self.rng.gauss(360, 120))
            duration = max(60, duration)
            failed = self.rng.random() < 0.03
            yield {
                "event": "deployment.finished",
                "at": pr["at"] + lag + duration,
                "deployment_id": f"dep_{dep_num:07d}",
                "outcome": "failed" if failed else "succeeded",
            }
            dep_num += 1

    def _emit_incidents(self, dep_events: list[dict], services: list[_Service]) -> Iterator[dict]:
        # Rough incident rate per 100 deploys.
        deps_started = [e for e in dep_events if e["event"] == "deployment.started"]
        expected = len(deps_started) * self.config.incident_rate_per_100_deploys / 100.0
        incident_count = max(0, int(round(expected)))
        picks = self.rng.sample(deps_started, min(incident_count, len(deps_started)))
        for i, dep in enumerate(picks, 1):
            declared_at = dep["at"] + self.rng.randint(600, 7200)
            severity = self.rng.choice(["sev4", "sev3", "sev3", "sev2", "sev1"])
            mitigated_at = declared_at + int(self.rng.gauss(3200, 1800))
            mitigated_at = max(declared_at + 300, mitigated_at)
            yield {
                "event": "incident.declared",
                "at": declared_at,
                "incident_id": f"inc_{i:05d}",
                "severity": severity,
                "service_id": dep["service_id"],
                "linked_deployment_id": dep["deployment_id"],
            }
            yield {
                "event": "incident.mitigated",
                "at": mitigated_at,
                "incident_id": f"inc_{i:05d}",
            }

    def _emit_engineering_changes(self, pr_events: list[dict]) -> Iterator[dict]:
        # Group PRs by author + day and treat runs of >=2 related PRs as one Engineering Change.
        opened = [e for e in pr_events if e["event"] == "pull_request.opened"]
        by_bucket: dict[tuple, list[dict]] = {}
        for e in opened:
            day_bucket = e["at"] // SECONDS_PER_DAY
            by_bucket.setdefault((e["author_id"], day_bucket), []).append(e)
        ec_num = 1
        for (author, day_bucket), events in by_bucket.items():
            if len(events) == 1:
                # Single PR = single Engineering Change with confidence 1.0
                pr_ids = [events[0]["pr_id"]]
                yield {
                    "engineering_change_id": f"ec_{ec_num:06d}",
                    "author_id": author,
                    "pr_ids": pr_ids,
                    "reconstruction_confidence": 1.0,
                    "opened_at": events[0]["at"],
                }
                ec_num += 1
            else:
                # Multi-PR: probabilistic linkage on some, deterministic on others
                pr_ids = [e["pr_id"] for e in events]
                # confidence lower when many PRs in the same day (noisier grouping)
                confidence = round(max(0.55, 1.0 - 0.08 * (len(events) - 1)), 2)
                yield {
                    "engineering_change_id": f"ec_{ec_num:06d}",
                    "author_id": author,
                    "pr_ids": pr_ids,
                    "reconstruction_confidence": confidence,
                    "opened_at": min(e["at"] for e in events),
                }
                ec_num += 1

    # ---- Orchestration ----

    def generate(self, out_dir: Path) -> dict[str, int]:
        out_dir.mkdir(parents=True, exist_ok=True)
        teams = self._make_teams()
        actors = self._make_actors(teams)
        services = self._make_services(teams)

        pr_events = list(self._emit_prs(actors, services))
        ci_events = list(self._emit_ci_runs(pr_events))
        deployments = list(self._emit_deployments(pr_events, services))
        incidents = list(self._emit_incidents(deployments, services))
        changes = list(self._emit_engineering_changes(pr_events))

        counts: dict[str, int] = {}
        counts["teams"] = _write_jsonl(out_dir / "teams.jsonl", [_dc_dict(t) for t in teams])
        counts["actors"] = _write_jsonl(out_dir / "actors.jsonl", [_dc_dict(a) for a in actors])
        counts["services"] = _write_jsonl(out_dir / "services.jsonl", [_dc_dict(s) for s in services])
        counts["pull_requests"] = _write_jsonl(out_dir / "pull_requests.jsonl", pr_events)
        counts["ci_runs"] = _write_jsonl(out_dir / "ci_runs.jsonl", ci_events)
        counts["deployments"] = _write_jsonl(out_dir / "deployments.jsonl", deployments)
        counts["incidents"] = _write_jsonl(out_dir / "incidents.jsonl", incidents)
        counts["engineering_changes"] = _write_jsonl(
            out_dir / "engineering_changes.jsonl", changes)
        return counts


# ---- Helpers ----

def _dc_dict(dc_instance) -> dict:
    from dataclasses import asdict
    return asdict(dc_instance)


def _write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def _poisson(rng: random.Random, lam: float) -> int:
    """Knuth's algorithm for a small-λ Poisson variate."""
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= rng.random()
        if p < L:
            return k - 1
