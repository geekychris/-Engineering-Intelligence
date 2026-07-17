# %% [markdown]
# # Context-switch cost for a team
#
# Reproduces the Ch 4 worked example: quantifying how much a team pays
# annually in attention-recovery overhead, and what a meeting-consolidation
# intervention would save.

# %%
import numpy as np
import matplotlib.pyplot as plt

# Team parameters
team_size = 8
loaded_hourly_rate = 145.0
working_days_per_year = 230

# Baseline observed values
baseline_switches_per_day = 3.4
baseline_recovery_minutes = 11.5

# Post-intervention observed values
after_switches_per_day = 2.1
after_recovery_minutes = 10.8

# %%
def annual_recovery_cost(team_n, rate, days,
                         switches_per_day, minutes_per_switch):
    per_engineer_per_day = switches_per_day * (minutes_per_switch / 60.0) * rate
    return team_n * per_engineer_per_day * days

baseline_cost = annual_recovery_cost(team_size, loaded_hourly_rate,
                                     working_days_per_year,
                                     baseline_switches_per_day,
                                     baseline_recovery_minutes)
after_cost = annual_recovery_cost(team_size, loaded_hourly_rate,
                                  working_days_per_year,
                                  after_switches_per_day,
                                  after_recovery_minutes)
savings = baseline_cost - after_cost

print(f"Baseline annual cost:      ${baseline_cost:>12,.0f}")
print(f"Post-intervention cost:    ${after_cost:>12,.0f}")
print(f"Estimated annual savings:  ${savings:>12,.0f}")

# %%
# Attention debt curve: fraction of pre-interruption effectiveness recovered
# over time. From the exponential-recovery model in Ch 4.
t = np.linspace(0, 45, 400)
recovery = 1 - 0.85 * np.exp(-t / 12)

fig, ax = plt.subplots(figsize=(8, 4.2))
ax.plot(t, recovery, color="#17365D", linewidth=2.4)
ax.fill_between(t, recovery, 1.0, color="#B78331", alpha=0.18,
                label="Attention debt")
ax.axhline(1.0, color="#17365D", linewidth=0.8, linestyle=":", alpha=0.5)
ax.set_xlabel("Minutes since interruption")
ax.set_ylabel("Fraction of pre-interruption effectiveness")
ax.set_title("Recovery after a context switch is gradual, not instant")
ax.set_ylim(0, 1.05)
ax.grid(True, alpha=0.2)
ax.legend(loc="lower right")
plt.tight_layout()
plt.show()

# %%
# Sensitivity: how sensitive is the annual saving to the assumed switch count?
switches_grid = np.linspace(1.5, 4.5, 30)
costs_at_baseline_recovery = [
    annual_recovery_cost(team_size, loaded_hourly_rate, working_days_per_year,
                         s, baseline_recovery_minutes)
    for s in switches_grid
]

fig, ax = plt.subplots(figsize=(8, 4.2))
ax.plot(switches_grid, costs_at_baseline_recovery,
        color="#17365D", linewidth=2.2)
ax.axvline(baseline_switches_per_day, color="#B78331", linestyle="--",
           label=f"Baseline ({baseline_switches_per_day} switches/day)")
ax.axvline(after_switches_per_day, color="#245A88", linestyle="--",
           label=f"Post-intervention ({after_switches_per_day} switches/day)")
ax.set_xlabel("Switches per engineer per day")
ax.set_ylabel("Annual recovery cost, team of 8 ($)")
ax.set_title("Recovery cost scales linearly with switch count")
ax.grid(True, alpha=0.2)
ax.legend()
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Interpretation
#
# The measurable saving here is roughly $73k/year for one 8-person team.
# The number is sensitive to switch count and loaded rate — check both
# against your own instrumentation before quoting it.
