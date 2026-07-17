# %% [markdown]
# # Computing the Cognitive Offload Index and its quality-adjusted form
#
# Ch 7. Whether an AI reviewer creates net cognitive offload — or just
# shifts work into verification and rework — requires accounting for
# time saved AND time spent triaging AI output.

# %%
import numpy as np
import matplotlib.pyplot as plt

# %%
# Per-PR measurements observed in a controlled rollout
baseline_review_time = 17.2       # minutes/PR in control
treatment_review_time = 13.9      # minutes/PR in treated cohort
author_ai_triage_time = 1.4       # additional author minutes per PR
reviewer_verification_time = 1.1  # additional reviewer minutes per PR
extra_rework_probability = 0.06   # 6% of PRs enter an additional rework cycle
extra_rework_minutes = 6.7        # cost of that extra cycle when it occurs

# Guardrail: quality-retention factor
escaped_defect_rate_baseline = 0.020
escaped_defect_rate_treatment = 0.0184

# %%
def net_saving_per_pr(baseline, treatment,
                      triage, verification,
                      rework_prob, rework_min):
    direct_saving = baseline - treatment
    extra = triage + verification + rework_prob * rework_min
    return direct_saving - extra

net = net_saving_per_pr(baseline_review_time, treatment_review_time,
                        author_ai_triage_time,
                        reviewer_verification_time,
                        extra_rework_probability,
                        extra_rework_minutes)
print(f"Direct review-time saving:  {baseline_review_time - treatment_review_time:+.2f} min/PR")
print(f"Author AI triage cost:       -{author_ai_triage_time:.2f} min/PR")
print(f"Reviewer verification cost:  -{reviewer_verification_time:.2f} min/PR")
print(f"Expected extra rework cost:  -{extra_rework_probability * extra_rework_minutes:.2f} min/PR")
print(f"Net cognitive offload:       {net:+.2f} min/PR "
      f"({100 * net / baseline_review_time:+.1f}% vs baseline)")

# %%
# QCOI (quality-adjusted): multiply by Q_r = 1 + (defect_rate_baseline - treatment) / baseline
q_r = 1.0 + (escaped_defect_rate_baseline - escaped_defect_rate_treatment) / escaped_defect_rate_baseline
qcoi = (net / baseline_review_time) * q_r
print(f"Quality retention factor Q_r: {q_r:.3f}")
print(f"QCOI (quality-adjusted):      {qcoi:+.3f}")

# %%
# Sensitivity: how much extra verification time would drive net to zero?
verification_grid = np.linspace(0, 4.0, 200)
saving = (baseline_review_time - treatment_review_time
          - author_ai_triage_time
          - verification_grid
          - extra_rework_probability * extra_rework_minutes)
break_even = verification_grid[np.argmin(np.abs(saving))]

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(verification_grid, saving, color="#17365D", linewidth=2.4)
ax.axhline(0, color="#6C371F", linewidth=1.0)
ax.axvline(reviewer_verification_time, color="#B78331", linestyle="--",
           label=f"Observed ({reviewer_verification_time} min)")
ax.axvline(break_even, color="#245A88", linestyle=":",
           label=f"Break-even ({break_even:.2f} min)")
ax.set_xlabel("Reviewer AI-finding verification time (min/PR)")
ax.set_ylabel("Net cognitive saving (min/PR)")
ax.set_title("Small increases in verification burden eliminate the net saving")
ax.legend()
ax.grid(True, alpha=0.2)
plt.tight_layout()
plt.show()
