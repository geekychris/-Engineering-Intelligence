# %% [markdown]
# # Queueing cost of a constrained resource
#
# Reproduces the worked example in Chapter 2 on queueing delay under
# an M/M/1 model. Edit the parameters below and see how expected wait
# time (and its cost) changes with utilisation.

# %%
import numpy as np
import matplotlib.pyplot as plt

# Parameters — edit these to match your context
service_time_minutes = 30.0     # mean time to complete one unit of work
loaded_hourly_rate = 145.0      # loaded cost per engineer-hour, USD
requests_per_day = 34.0         # arrival rate against the resource
work_hours_per_day = 24.0       # available hours per day across the resource pool

# %%
# Utilisation ρ = arrival rate / service rate.
service_rate_per_hour = 60.0 / service_time_minutes
capacity_per_day = service_rate_per_hour * work_hours_per_day
utilisation = requests_per_day / capacity_per_day

print(f"Service rate:      {service_rate_per_hour:.1f} requests/hour")
print(f"Daily capacity:    {capacity_per_day:.0f} requests/day")
print(f"Utilisation ρ:     {utilisation:.2%}")

# %%
# Expected M/M/1 wait time in the queue (Little's Law + M/M/1 result).
# W_q = service_time * ρ / (1 - ρ)
if utilisation >= 1.0:
    raise SystemExit("Arrival rate exceeds capacity; queue grows without bound.")
expected_wait_minutes = service_time_minutes * utilisation / (1.0 - utilisation)

# Daily cost in wasted human time (arrivals × mean wait × rate).
daily_queue_cost = requests_per_day * (expected_wait_minutes / 60.0) * loaded_hourly_rate
annual_queue_cost = daily_queue_cost * 250.0

print(f"Expected wait:     {expected_wait_minutes:.1f} minutes per request")
print(f"Daily queue cost:  ${daily_queue_cost:,.0f}")
print(f"Annualised cost:   ${annual_queue_cost:,.0f}")

# %%
# Sensitivity curve: same operating point but sweep utilisation from 5% to 95%.
rho = np.linspace(0.05, 0.95, 400)
wait = service_time_minutes * rho / (1.0 - rho)
daily_cost_curve = (requests_per_day * wait / 60.0) * loaded_hourly_rate

fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.plot(rho, wait, color="#17365D", linewidth=2.2, label="Expected wait (min)")
ax.axvline(utilisation, color="#B78331", linestyle="--", linewidth=1.2,
           label=f"You are here (ρ = {utilisation:.2f})")
ax.set_xlabel("Utilisation ρ of the constrained resource")
ax.set_ylabel("Expected queue wait (minutes)")
ax.set_title("Queueing delay grows non-linearly with utilisation")
ax.set_ylim(0, min(400, wait[-1]))
ax.grid(True, alpha=0.2)
ax.legend()
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Interpretation
#
# The book's worked example uses `service_time=30 min`, arrival that produces
# roughly 70% utilisation, and a loaded rate of $145/hour. The mean wait is
# short at 70% and explodes past 85%.
#
# Adjust `requests_per_day` upward and re-run: you'll see queue wait — and its
# daily cost — grow faster than the arrival rate. That is the queueing
# penalty for operating a constrained resource close to saturation.
