# engintel-synth

Synthetic engineering telemetry generator. Emits realistic-shaped events
across a fictional multi-team engineering organisation so companion
notebooks (and any downstream reconstruction, metric, or experiment work)
have a substrate to operate on without needing a real organisation's data.

## What it emits

- `actors.jsonl` — people, service accounts, bots, and AI agents with
  team and role assignments over time.
- `teams.jsonl` — team roster and ownership assignments per time interval.
- `services.jsonl` — service catalogue with dependencies, ownership,
  and blast-radius attributes.
- `pull_requests.jsonl` — pull-request lifecycle events (opened, review
  requested, review submitted, comment, merged, closed).
- `ci_runs.jsonl` — CI pipeline events (started, passed, failed) linked
  to pull requests.
- `deployments.jsonl` — deployment lifecycle events across services.
- `incidents.jsonl` — production incidents with severity, service
  affected, and time-to-mitigate.
- `engineering_changes.jsonl` — Engineering-Change groupings that link
  intents to their pull requests, deployments, and outcomes with
  reconstruction confidence.

Everything is JSON Lines with a stable schema. See `SCHEMA.md` for
field-level detail.

## Usage

```
pip install -e companion/synth
python -m engintel_synth --days 60 --teams 30 --seed 42 --out data/
```

Output lands in `data/` as one `.jsonl` file per stream.

Determinism: the same `--seed` produces the same files byte-for-byte.
Bump `--days` or `--teams` to scale up; `--seed` is what changes the
population.

## Design principles

- No external dependencies. Standard library only.
- Deterministic under a seed.
- Populations sized so a laptop can generate 60 days × 40 teams in seconds.
- Enough realism that the numbers in the book's worked examples become
  reproducible against the generated corpus.

## Not a real production dataset

Everything here is invented. Names are drawn from a small pool; the
scenarios are illustrative. Do not treat any pattern in the output as
evidence about real engineering organisations.
