# %% [markdown]
# # Bayesian updating for a small-sample metric
#
# Ch 5. For rare-outcome or small-population metrics, a Bayesian estimate
# gives more useful decision support than a frequentist point estimate,
# because it lets us report probabilities like "P(rate > 3%) = 0.12"
# rather than only intervals.

# %%
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta as beta_dist

from engintel_utils.stats import beta_binomial_posterior

# %%
# Weak Beta(1, 1) uniform prior, updated by observed data.
# Suppose we observed 47 changes in a repository with 3 escaped defects.
mean, ci = beta_binomial_posterior(successes=3, trials=47)
print(f"Posterior mean escape rate: {mean:.4f}")
print(f"Credible interval: {ci}")

# %%
# Compare a Beta(1,1) uniform prior against a stronger Beta(3, 97) prior
# reflecting a company-wide expectation that escape rate is roughly 3%.
priors = [
    ("uniform Beta(1,1)", 1.0, 1.0),
    ("informative Beta(3, 97)", 3.0, 97.0),
]

fig, ax = plt.subplots(figsize=(9, 4.5))
x = np.linspace(0, 0.20, 400)
for label, alpha_p, beta_p in priors:
    alpha_post = alpha_p + 3
    beta_post = beta_p + 47 - 3
    y = beta_dist.pdf(x, alpha_post, beta_post)
    mean_post = alpha_post / (alpha_post + beta_post)
    ax.plot(x, y, linewidth=2.2, label=f"{label} → posterior mean {mean_post:.3f}")
ax.set_xlabel("Escape rate")
ax.set_ylabel("Posterior density")
ax.set_title("Prior strength moves the posterior estimate")
ax.legend()
ax.grid(True, alpha=0.2)
plt.tight_layout()
plt.show()

# %%
# Decision-support question: "what is the probability the true rate
# exceeds our 3% acceptance threshold?"
threshold = 0.03
for label, alpha_p, beta_p in priors:
    alpha_post = alpha_p + 3
    beta_post = beta_p + 47 - 3
    prob = 1 - beta_dist.cdf(threshold, alpha_post, beta_post)
    print(f"{label:>28}: P(rate > {threshold:.2f}) = {prob:.3f}")
