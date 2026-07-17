# %% [markdown]
# # Reading the flow bundle without misreading it
#
# Reproduces the Ch 11 worked example: every headline flow metric moves
# in the desired direction, but the accepted-outcome rate falls four
# points. Bundle-level interpretation catches what any single number
# would hide.

# %%
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np

@dataclass
class FlowBundle:
    label: str
    lead_time_days: float
    active_time_days: float
    review_queue_days: float
    ci_queue_days: float
    staging_queue_days: float
    wip: int
    aging_p95_days: float
    flow_efficiency: float
    accepted_outcome_rate: float

before = FlowBundle(
    label="Before",
    lead_time_days=7.9,
    active_time_days=3.2,
    review_queue_days=2.6,
    ci_queue_days=0.7,
    staging_queue_days=0.9,
    wip=51,
    aging_p95_days=27,
    flow_efficiency=0.41,
    accepted_outcome_rate=0.91,
)
after = FlowBundle(
    label="After",
    lead_time_days=6.2,
    active_time_days=3.1,
    review_queue_days=1.4,
    ci_queue_days=0.7,
    staging_queue_days=1.0,
    wip=42,
    aging_p95_days=18,
    flow_efficiency=0.50,
    accepted_outcome_rate=0.87,
)

# %%
def pct_delta(a: float, b: float) -> str:
    if a == 0:
        return "n/a"
    return f"{(b - a) / a:+.1%}"

metrics = [
    ("Lead time (days)", before.lead_time_days, after.lead_time_days, "lower_better"),
    ("Active time (days)", before.active_time_days, after.active_time_days, "lower_better"),
    ("Review queue (days)", before.review_queue_days, after.review_queue_days, "lower_better"),
    ("CI queue (days)", before.ci_queue_days, after.ci_queue_days, "lower_better"),
    ("Staging queue (days)", before.staging_queue_days, after.staging_queue_days, "lower_better"),
    ("WIP", before.wip, after.wip, "lower_better"),
    ("Aging p95 (days)", before.aging_p95_days, after.aging_p95_days, "lower_better"),
    ("Flow efficiency", before.flow_efficiency, after.flow_efficiency, "higher_better"),
    ("Accepted outcome rate", before.accepted_outcome_rate, after.accepted_outcome_rate, "higher_better"),
]
print(f"{'Metric':30}{'Before':>10}{'After':>10}{'Δ%':>10}   Signal")
print("-" * 78)
for label, b, a, direction in metrics:
    delta = pct_delta(b, a)
    good = ((direction == "lower_better" and a < b)
            or (direction == "higher_better" and a > b))
    signal = "improve" if good else "REGRESSED"
    print(f"{label:30}{b:>10.2f}{a:>10.2f}{delta:>10}   {signal}")

# %%
# Highlight the accepted-outcome regression on a single chart.
labels = [m[0] for m in metrics]
before_vals = [m[1] for m in metrics]
after_vals = [m[2] for m in metrics]
# Normalise each metric to before=1 to compare movement on one axis.
norm = np.array([a / b for _, b, a, _ in metrics])
colors = ["#17365D" if n <= 1 else "#6C371F" for n in norm]

fig, ax = plt.subplots(figsize=(10, 4.5))
ax.axhline(1.0, color="#B78331", linewidth=1.0, linestyle="--")
ax.bar(labels, norm, color=colors, alpha=0.85)
ax.set_ylabel("After ÷ Before (1.0 = no change)")
ax.set_title("Bundle read: seven metrics improve, accepted-outcome regresses")
ax.tick_params(axis="x", rotation=30)
for tick in ax.get_xticklabels():
    tick.set_ha("right")
ax.grid(True, alpha=0.2, axis="y")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Interpretation
#
# Six metrics moved in the desired direction; the accepted-outcome rate did
# not. Bundle-level interpretation makes the trade-off legible: the workflow
# change is not simply "good," it is faster with a quality cost that has to
# be paid attention to. The next step is to drill down on the accepted-outcome
# delta to find which category of change is being reverted more, and to
# amend the routing rule rather than to reverse it wholesale.
