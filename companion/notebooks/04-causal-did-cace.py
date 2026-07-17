# %% [markdown]
# # Difference-in-differences and complier-average causal effect
#
# Reproduces the Ch 6 worked example: did the AI reviewer actually reduce
# review latency, or did the naive before-after comparison overstate its
# effect?

# %%
import numpy as np
import matplotlib.pyplot as plt

# Observed cell means (hours of mean review latency)
Y_T_before = 5.6
Y_T_after = 4.9
Y_C_before = 6.4
Y_C_after = 6.8

# Exposure: what fraction of assigned teams actually used the AI reviewer?
exposure_rate = 0.71

# %%
# 1. Naive before-after in the treatment group
naive = Y_T_before - Y_T_after
print(f"Naive before-after gap (treatment only): {naive:+.2f} hours "
      f"({-naive/Y_T_before:.1%} apparent improvement)")

# 2. Difference-in-differences
did = (Y_T_after - Y_T_before) - (Y_C_after - Y_C_before)
print(f"Difference-in-differences estimate:      {did:+.2f} hours")

# 3. Complier-average causal effect (Wald / IV under one-sided noncompliance)
cace = did / exposure_rate
print(f"Complier-average causal effect (CACE):   {cace:+.2f} hours "
      f"(rescaled by {exposure_rate:.2f} exposure)")

# %%
# Visualise the four-cell comparison
fig, ax = plt.subplots(figsize=(7.5, 4.2))
x = np.array([0, 1])
ax.plot(x, [Y_T_before, Y_T_after], "o-", color="#17365D", linewidth=2.4,
        markersize=8, label="Treated teams")
ax.plot(x, [Y_C_before, Y_C_after], "s--", color="#B78331", linewidth=2.4,
        markersize=8, label="Control teams")
# Draw the counterfactual control-trend line for the treated group
counterfactual_T_after = Y_T_before + (Y_C_after - Y_C_before)
ax.plot([1, 1], [Y_T_after, counterfactual_T_after],
        color="#6C371F", linewidth=1.2)
ax.annotate("DiD effect", xy=(1.02, (Y_T_after + counterfactual_T_after) / 2),
            color="#6C371F")
ax.set_xticks(x)
ax.set_xticklabels(["Before", "After"])
ax.set_ylabel("Mean review latency (hours)")
ax.set_title("DiD compares deltas, not levels")
ax.grid(True, alpha=0.2)
ax.legend()
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Interpretation
#
# The naive comparison overstates the effect by about 70%. The DiD estimate
# credits the AI reviewer with -1.1 hours; the CACE rescales that to -1.55
# hours _among those who actually engaged with the tool_. Which estimand
# belongs in the executive summary depends on the decision — a mandate needs
# ITT/DiD; a voluntary adoption path needs CACE. Reporting only one is a
# recipe for mispricing the rollout.
