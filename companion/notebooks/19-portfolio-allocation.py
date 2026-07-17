# %% [markdown]
# # Portfolio allocation under capacity and mandatory constraints
#
# Ch 14. When one initiative is mandatory and the others compete for
# remaining capacity, the optimal allocation is not the highest-ROI item —
# it's whatever fits after the floor is paid.

# %%
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np

@dataclass
class Initiative:
    name: str
    expected_value_usd: float
    general_engineer_quarters: float
    specialist_quarters: float
    cost_of_delay_per_month: float
    mandatory: bool = False

initiatives = [
    Initiative("A: Payments migration",             8_000_000, 24, 3, 180_000, mandatory=False),
    Initiative("B: Developer platform upgrade",     4_000_000, 30, 0,  60_000, mandatory=False),
    Initiative("C: Regulatory compliance",         12_000_000, 18, 5, float("inf"), mandatory=True),
]

CAPACITY_GENERAL = 42
CAPACITY_SPECIALIST = 6

# %%
# Step 1: pay mandatory initiatives first.
remaining_general = CAPACITY_GENERAL
remaining_specialist = CAPACITY_SPECIALIST
funded = []
for i in initiatives:
    if i.mandatory:
        remaining_general -= i.general_engineer_quarters
        remaining_specialist -= i.specialist_quarters
        funded.append(i)
print(f"After mandatory: {remaining_general} general q, {remaining_specialist} specialist q remain")

# Step 2: rank the rest by expected-value-per-general-quarter.
optional = [i for i in initiatives if not i.mandatory]
optional.sort(
    key=lambda i: i.expected_value_usd / max(1, i.general_engineer_quarters),
    reverse=True,
)

# Step 3: greedy allocation subject to both resource constraints.
for i in optional:
    if (i.general_engineer_quarters <= remaining_general
            and i.specialist_quarters <= remaining_specialist):
        funded.append(i)
        remaining_general -= i.general_engineer_quarters
        remaining_specialist -= i.specialist_quarters

print(f"After optional: {remaining_general} general q, {remaining_specialist} specialist q remain")
print()
for i in funded:
    print(f"  ✓ {i.name}  (value ${i.expected_value_usd:,.0f})")

# %%
# Compute the opportunity cost of any deferred initiative.
deferred = [i for i in initiatives if i not in funded]
if deferred:
    print("Deferred:")
    for i in deferred:
        months_delay = 3   # deferred by one quarter
        cost_of_delay = i.cost_of_delay_per_month * months_delay
        print(f"  ✗ {i.name}: value ${i.expected_value_usd:,.0f}, "
              f"cost of delay ${cost_of_delay:,.0f} for one quarter")

# %%
# Visualise the allocation.
names = [i.name for i in initiatives]
general = [i.general_engineer_quarters for i in initiatives]
specialist = [i.specialist_quarters for i in initiatives]
funded_names = {i.name for i in funded}
colors = ["#17365D" if n in funded_names else "#6C371F" for n in names]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
ax1.bar(names, general, color=colors)
ax1.axhline(CAPACITY_GENERAL, color="#B78331", linestyle="--",
            label=f"Capacity ({CAPACITY_GENERAL})")
ax1.set_ylabel("General engineer-quarters")
ax1.set_title("General capacity")
ax1.tick_params(axis="x", rotation=15)
ax1.legend()

ax2.bar(names, specialist, color=colors)
ax2.axhline(CAPACITY_SPECIALIST, color="#B78331", linestyle="--",
            label=f"Capacity ({CAPACITY_SPECIALIST})")
ax2.set_ylabel("Specialist quarters")
ax2.set_title("Specialist capacity")
ax2.tick_params(axis="x", rotation=15)
ax2.legend()
plt.tight_layout()
plt.show()
