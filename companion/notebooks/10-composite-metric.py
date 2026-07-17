# %% [markdown]
# # Building a composite metric that preserves drill-down
#
# Ch 5. Construct a Review Friction Index (RFI) from standardized
# components and demonstrate why users must be able to inspect the
# component values, not just the composite score.

# %%
import numpy as np
import matplotlib.pyplot as plt

from engintel_utils.metrics import CompositeMetric, zscore

# %%
rng = np.random.default_rng(20260101)
n = 500

# Simulated per-PR features
queue_age_hours = rng.gamma(2.5, 2.4, n)
response_cycles = rng.poisson(2.0, n)
unresolved_comments = rng.poisson(1.4, n)
context_recovery_events = rng.poisson(1.0, n)
validation_effort_minutes = rng.gamma(2.0, 4.0, n)

# Standardise each component
components = {
    "queue_age": zscore(queue_age_hours),
    "response_cycles": zscore(response_cycles),
    "unresolved_comments": zscore(unresolved_comments),
    "context_recovery": zscore(context_recovery_events),
    "validation_effort": zscore(validation_effort_minutes),
}

weights = {
    "queue_age": 0.30,
    "response_cycles": 0.20,
    "unresolved_comments": 0.15,
    "context_recovery": 0.20,
    "validation_effort": 0.15,
}

rfi = np.zeros(n)
for k, series in components.items():
    rfi += weights[k] * series

# %%
# Two PRs at the 90th percentile of RFI — different underlying reasons.
threshold = np.quantile(rfi, 0.90)
top = np.argsort(rfi)[-10:][::-1]
print(f"90th percentile RFI: {threshold:.2f}")
print()
for idx in top[:3]:
    print(f"PR #{idx}:  RFI={rfi[idx]:+.2f}")
    for k, series in components.items():
        print(f"    {k:>22}: z = {series[idx]:+.2f}")
    print()

# %% [markdown]
# The two top-friction PRs are both flagged by the composite score, but
# their component profiles differ dramatically. Aggregating without the
# ability to inspect components leads to intervening on the wrong friction
# source — that is the failure mode the Ch 5 discussion warns about.

# %%
# Show component contributions for the top 20 PRs as a stacked chart.
top20 = np.argsort(rfi)[-20:][::-1]
contribs = {k: weights[k] * components[k][top20] for k in components}
fig, ax = plt.subplots(figsize=(10, 4.5))
bottoms = np.zeros(20)
colors = ["#17365D", "#245A88", "#8FC0E8", "#B78331", "#6C371F"]
for c, (k, contrib) in zip(colors, contribs.items()):
    ax.bar(range(20), contrib, bottom=bottoms, label=k, color=c)
    bottoms += contrib
ax.set_xlabel("Top-20 PRs by RFI (rank)")
ax.set_ylabel("Component contribution to RFI")
ax.set_title("Composite metric decomposed by component")
ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.28))
plt.tight_layout()
plt.show()
