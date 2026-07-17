# %% [markdown]
# # Metric versioning: measuring what a definition change costs
#
# Ch 5. When a metric definition changes, the "improvement" it appears to
# produce is a mix of a real signal and a definition artefact. Version
# every consequential metric and recompute both series over a look-back
# window before declaring victory.

# %%
import numpy as np
import matplotlib.pyplot as plt

from engintel_utils.metrics import MetricSpec, compare_metric_versions

# %%
spec_v1 = MetricSpec(
    identifier="review_latency",
    title="Mean review latency",
    version="1.0.0",
    construct="time to first substantive review",
    decision="reviewer-capacity investment",
    unit_of_analysis="pull_request",
    formula="mean(first_review_at - opened_at)",
    guardrails=["escaped-defect rate"],
    owner="platform-metrics",
)

# In April the metric owner changes the population definition: exclude
# drafts and bot-authored dependency bumps. Bump minor version.
spec_v2 = spec_v1.bump(
    "minor",
    "Exclude draft and bot-authored dependency bumps from the population.",
)
print(spec_v2.version)
print(spec_v2.notes)

# %%
rng = np.random.default_rng(42)
n_prs = 12_000

# Simulate a population where drafts and bot bumps have longer latency,
# so excluding them makes the metric appear smaller regardless of any
# real workflow change.
is_bot_or_draft = rng.random(n_prs) < 0.22
latency_hours = np.where(
    is_bot_or_draft,
    rng.gamma(shape=3.0, scale=2.5, size=n_prs),      # 7.5h mean, longer tail
    rng.gamma(shape=3.0, scale=1.3, size=n_prs),      # 3.9h mean
)

# Under v1 all PRs count.
values_v1 = latency_hours
# Under v2, drafts and bot bumps are excluded from the population; simulate
# by masking those to NaN and computing the metric over the remainder.
values_v2 = latency_hours.copy()
values_v2[is_bot_or_draft] = np.nan

v1_mean = np.nanmean(values_v1)
v2_mean = np.nanmean(values_v2)
print(f"v1 population mean: {v1_mean:.2f} h")
print(f"v2 population mean: {v2_mean:.2f} h")
print(f"Definitional shift: {v2_mean - v1_mean:+.2f} h "
      f"({100 * (v2_mean - v1_mean) / v1_mean:+.1f}%)")

# %%
# What if a genuine workflow intervention also shrinks review latency by
# a modest 8% at the same time? The two shifts are entangled.
real_effect = -0.08
latency_after = latency_hours * (1 + real_effect)
v1_after = np.nanmean(latency_after)
v2_after = np.nanmean(np.where(is_bot_or_draft, np.nan, latency_after))
print()
print(f"After the workflow change:")
print(f"  v1-consistent (all PRs):    {v1_after:.2f} h ({100*(v1_after-v1_mean)/v1_mean:+.1f}%)")
print(f"  v2-consistent (new pop):    {v2_after:.2f} h ({100*(v2_after-v2_mean)/v2_mean:+.1f}%)")
print(f"  Naive v1→v2 comparison:     {v2_after - v1_mean:+.2f} h "
      f"({100*(v2_after-v1_mean)/v1_mean:+.1f}%)")

# %%
fig, ax = plt.subplots(figsize=(8, 4.5))
labels = ["v1 baseline", "v2 baseline",
          "v1 after intervention", "v2 after intervention",
          "naive v1→v2 comparison"]
values = [v1_mean, v2_mean, v1_after, v2_after, v2_after]
colors = ["#17365D", "#245A88", "#17365D", "#245A88", "#6C371F"]
alphas = [1.0, 1.0, 0.7, 0.7, 1.0]
ax.bar(labels, values, color=colors, alpha=None)
for i, (bar, a) in enumerate(zip(ax.patches, alphas)):
    bar.set_alpha(a)
ax.axhline(v1_mean, color="#B78331", linestyle="--", linewidth=1.0)
ax.set_ylabel("Mean review latency (hours)")
ax.set_title("Definition change and real change are entangled without versioning")
ax.tick_params(axis="x", rotation=15)
plt.tight_layout()
plt.show()
