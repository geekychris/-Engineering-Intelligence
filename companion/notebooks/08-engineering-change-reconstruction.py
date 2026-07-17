# %% [markdown]
# # Reconstructing Engineering Changes from raw events
#
# Ch 3. Given a stream of pull-request events (from `engintel-synth` or
# your own instrumentation), group them into Engineering Changes with
# reconstruction confidence.

# %%
from pathlib import Path
import subprocess
import sys

from engintel_utils.reconstruction import (
    load_jsonl, reconstruct_changes, reconstruction_summary,
)

# %%
# Generate a synthetic dataset if one isn't already on disk.
data_dir = Path("/tmp/engintel-recon-demo")
if not (data_dir / "pull_requests.jsonl").exists():
    subprocess.run([sys.executable, "-m", "engintel_synth",
                    "--days", "14", "--teams", "10", "--seed", "42",
                    "--out", str(data_dir)], check=True)

pr_events = load_jsonl(data_dir / "pull_requests.jsonl")
print(f"Loaded {len(pr_events):,} pull-request events")

# %%
changes = reconstruct_changes(pr_events)
summary = reconstruction_summary(changes)
print("Reconstruction summary:")
for k, v in summary.items():
    print(f"  {k:>28}: {v}")

# %%
# Pick a low-confidence change and inspect it.
low_conf = sorted(changes, key=lambda c: c.confidence)[:5]
for c in low_conf:
    print(f"{c.id}  author={c.author_id}  confidence={c.confidence:.2f}  "
          f"pr_count={len(c.pr_ids)}  linkage={c.linkage}")

# %% [markdown]
# ## Interpretation
#
# The reconstruction confidence gives every downstream metric an
# uncertainty budget. Aggregations weighted by confidence produce
# "deterministic-only" floor estimates alongside "all evidence" ceiling
# estimates, matching the pattern in the Ch 3 worked example.
