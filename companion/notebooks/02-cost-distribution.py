# %% [markdown]
# # Cost distribution — median vs mean
#
# Reproduces the Ch 2 discussion of right-skewed cost distributions and
# why policies tuned to the mean systematically over- or under-invest.

# %%
import numpy as np
import matplotlib.pyplot as plt

# Log-normal parameters chosen to yield a plausible cost distribution
# for an Engineering Change: median around $2,200, heavy tail out to
# tens of thousands.
rng = np.random.default_rng(20260716)
mu = np.log(2200)      # median = exp(mu)
sigma = 0.85           # spread
n = 20_000
samples = rng.lognormal(mean=mu, sigma=sigma, size=n)

# %%
median = float(np.median(samples))
mean = float(np.mean(samples))
p90 = float(np.quantile(samples, 0.90))
p99 = float(np.quantile(samples, 0.99))

print(f"Sample size:     {n:,}")
print(f"Median:          ${median:,.0f}")
print(f"Mean:            ${mean:,.0f}")
print(f"90th percentile: ${p90:,.0f}")
print(f"99th percentile: ${p99:,.0f}")
print(f"Mean / median:   {mean / median:.2f}x")

# %%
# Show the distribution with median and mean marked.
p95 = np.quantile(samples, 0.95)
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.hist(samples[samples <= p95 * 1.5], bins=80, color="#17365D", alpha=0.75,
        edgecolor="#F5EBD6", linewidth=0.4)
ax.axvline(median, color="#B78331", linewidth=1.6, linestyle="--",
           label=f"Median ≈ ${median:,.0f}")
ax.axvline(mean, color="#6C371F", linewidth=1.6,
           label=f"Mean ≈ ${mean:,.0f}")
ax.set_xlabel("Cost per Engineering Change (US$)")
ax.set_ylabel("Number of changes")
ax.set_title("Right-skewed cost distribution: mean lies well above median")
ax.grid(True, alpha=0.2)
ax.legend()
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Interpretation
#
# The mean is ~40% higher than the median. A policy that reviews every change
# using average-cost assumptions will:
#
# - overspend on routine changes (which are below the mean);
# - underinvest in the tail (which drives most incidents and cost of delay).
#
# The book's recommendation is to report both statistics side-by-side and to
# tier policy by change class rather than by a single per-change budget.
