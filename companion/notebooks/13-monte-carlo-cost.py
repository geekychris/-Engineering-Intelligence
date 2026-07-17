# %% [markdown]
# # Monte Carlo simulation of total Engineering Change cost
#
# Ch 2. Point estimates hide uncertainty; a Monte Carlo simulation over
# uncertain component distributions gives the whole distribution of
# outcomes and shows which components dominate the tail.

# %%
import numpy as np
import matplotlib.pyplot as plt

from engintel_utils.monte_carlo import lognormal, triangular, sum_cost

# %%
# Component distributions calibrated to make the total median ~$5,000 with
# a heavy tail driven by risk-related outcomes.
components = [
    lognormal(mean_of_log=np.log(1600), sigma_of_log=0.55, name="human effort"),
    lognormal(mean_of_log=np.log(1000), sigma_of_log=0.40, name="tool and infra"),
    triangular(200, 700, 3000, name="coordination"),
    triangular(400, 1200, 5000, name="delay"),
    lognormal(mean_of_log=np.log(400), sigma_of_log=1.10, name="quality tail"),
    lognormal(mean_of_log=np.log(120), sigma_of_log=1.60, name="risk tail"),
]

diag = sum_cost(components, n=30_000, seed=42)
print("Simulation diagnostics:")
for k, v in diag.items():
    print(f"  {k:>8}: ${v:,.0f}")

# %%
rng = np.random.default_rng(42)
n = 30_000
component_samples = {c.name: c.sampler(rng, n) for c in components}
total = np.zeros(n)
for s in component_samples.values():
    total += s

# Draw the total distribution
fig, ax = plt.subplots(figsize=(8, 4.5))
p95 = np.quantile(total, 0.95)
ax.hist(total[total <= p95 * 1.4], bins=80, color="#17365D",
        alpha=0.78, edgecolor="#F5EBD6", linewidth=0.4)
ax.axvline(np.median(total), color="#B78331", linestyle="--", linewidth=1.6,
           label=f"Median ${np.median(total):,.0f}")
ax.axvline(total.mean(), color="#6C371F", linewidth=1.6,
           label=f"Mean ${total.mean():,.0f}")
ax.axvline(p95, color="#245A88", linestyle=":", linewidth=1.6,
           label=f"P95 ${p95:,.0f}")
ax.set_xlabel("Simulated Engineering Change cost (US$)")
ax.set_ylabel("Frequency")
ax.set_title("Total cost distribution across 30,000 Monte Carlo draws")
ax.legend()
plt.tight_layout()
plt.show()

# %%
# Tornado diagram: which component's variance matters most for the P95?
p95_total = np.quantile(total, 0.95)
contributions = {}
for name, samples in component_samples.items():
    # Estimate this component's contribution at the tail by looking at
    # its mean value among the top 5% total draws.
    tail_mask = total >= p95_total
    contributions[name] = samples[tail_mask].mean()

names = list(contributions.keys())
vals = [contributions[n] for n in names]
order = np.argsort(vals)
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.barh([names[i] for i in order], [vals[i] for i in order], color="#17365D")
for i, v in enumerate([vals[i] for i in order]):
    ax.text(v * 1.02, i, f"${v:,.0f}", va="center", color="#17365D")
ax.set_xlabel("Mean component value in top-5% total-cost draws (US$)")
ax.set_title("Tail-driver diagnostic — which component dominates the P95?")
plt.tight_layout()
plt.show()
