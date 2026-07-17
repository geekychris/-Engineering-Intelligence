"""CLI entry point for engintel_synth."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .generator import Config, Generator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="engintel-synth",
        description="Generate synthetic engineering telemetry.",
    )
    parser.add_argument("--days", type=int, default=30,
                        help="number of days of telemetry to emit (default 30)")
    parser.add_argument("--teams", type=int, default=20,
                        help="number of teams in the fictional organisation (default 20)")
    parser.add_argument("--seed", type=int, default=42,
                        help="deterministic seed (default 42)")
    parser.add_argument("--out", type=Path, default=Path("data"),
                        help="output directory (default ./data)")
    args = parser.parse_args(argv)

    if args.days <= 0 or args.teams <= 0:
        print("--days and --teams must be positive", file=sys.stderr)
        return 2

    config = Config(days=args.days, teams=args.teams, seed=args.seed)
    generator = Generator(config)
    counts = generator.generate(args.out)

    print(f"Wrote {sum(counts.values())} records to {args.out}/:")
    for name, n in counts.items():
        print(f"  {name:>22}: {n:>8} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
