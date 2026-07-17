# %% [markdown]
# # Statistical power and the minimum detectable effect
#
# Reproduces the Ch 6 discussion of how power scales with sample size.
# Type your own baseline standard deviation and desired MDE, and the
# notebook prints the required per-arm sample size and shows the power
# curves.

# %%
import numpy as np
import matplotlib.pyplot as plt
from math import sqrt
from statistics import NormalDist

# Design parameters
alpha = 0.05      # two-sided type-I error rate
beta = 0.20       # 1 - beta is desired power (0.80)
sigma = 42.0      # baseline standard deviation of the outcome (units of Y)
mde_absolute = 3.4  # smallest effect you care about detecting (units of Y)

# %%
z_alpha = NormalDist().inv_cdf(1 - alpha / 2)
z_beta = NormalDist().inv_cdf(1 - beta)

# Two-sample z-approximation: n per arm
n_per_arm = 2 * ((z_alpha + z_beta) * sigma / mde_absolute) ** 2

print(f"Type-I error α:           {alpha}")
print(f"Type-II error β:          {beta}  (power = {1-beta:.2f})")
print(f"Outcome σ:                {sigma}")
print(f"Target MDE:               {mde_absolute}")
print(f"Required per-arm sample:  {int(np.ceil(n_per_arm)):,}")

# %%
# Power curves for a range of sample sizes.
def two_sided_power(effect, n, sigma, alpha=0.05):
    se = sigma * np.sqrt(2.0 / n)
    z = NormalDist().inv_cdf(1 - alpha / 2)
    upper = np.array([NormalDist().cdf(z - d / se) for d in effect])
    lower = np.array([NormalDist().cdf(-z - d / se) for d in effect])
    return 1 - upper + lower

effect_grid = np.linspace(0, 20, 400)
sample_sizes = [500, 2_000, 8_000, 32_000]
colors = ["#8FC0E8", "#245A88", "#17365D", "#0E294D"]

fig, ax = plt.subplots(figsize=(8, 4.5))
for c, n in zip(colors, sample_sizes):
    ax.plot(effect_grid, two_sided_power(effect_grid, n, sigma),
            color=c, linewidth=2.0, label=f"n = {n:,} per arm")
ax.axhline(1 - beta, color="#B78331", linestyle="--", linewidth=1.4,
           label=f"Power = {1 - beta:.0%}")
ax.set_xlabel(f"Detectable effect size (same units as σ = {sigma})")
ax.set_ylabel("Power to detect the effect")
ax.set_title("MDE shrinks with sample size, not with hope")
ax.set_ylim(0, 1.05)
ax.grid(True, alpha=0.2)
ax.legend(loc="lower right")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Interpretation
#
# Type your organisation's outcome σ and the effect you actually care about
# into the top of this notebook. The required sample often surprises people
# — an 8% shift on a heavy-tailed outcome takes far more units than an
# executive rollout timetable assumes. Reporting the MDE alongside a
# negative result distinguishes "we didn't find an effect" from "we couldn't
# have found the effect we care about."
