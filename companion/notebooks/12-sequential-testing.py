# %% [markdown]
# # Sequential testing with an O'Brien-Fleming boundary
#
# Ch 6. Continuous experiments inspected repeatedly under a naive
# significance threshold inflate false positives. Use a group-sequential
# boundary that spends alpha over planned looks.

# %%
import numpy as np
import matplotlib.pyplot as plt

from engintel_utils.stats import obrien_fleming_boundary

# %%
K = 5           # number of planned looks
alpha = 0.05

boundary = obrien_fleming_boundary(K, alpha=alpha)
for i, z in enumerate(boundary, 1):
    print(f"Look {i} of {K}: reject H0 if |z| >= {z:.3f}")

# %%
# Simulate an experiment under the null hypothesis and count how many of
# 5,000 runs would falsely reject under the naive vs sequential rule.
rng = np.random.default_rng(42)
runs = 5_000
per_look_n = 200

naive_reject = 0
seq_reject = 0
for _ in range(runs):
    stopped = False
    for k in range(K):
        y = rng.normal(0.0, 1.0, per_look_n * (k + 1))
        z = y.mean() / (1.0 / np.sqrt(len(y)))
        if abs(z) >= 1.96 and not stopped:
            naive_reject += 1
            stopped = True
    stopped = False
    for k in range(K):
        y = rng.normal(0.0, 1.0, per_look_n * (k + 1))
        z = y.mean() / (1.0 / np.sqrt(len(y)))
        if abs(z) >= boundary[k] and not stopped:
            seq_reject += 1
            stopped = True

print(f"Naive repeated α=0.05: {naive_reject / runs:.3f} type-I error")
print(f"O'Brien-Fleming spend: {seq_reject / runs:.3f} type-I error")

# %%
fig, ax = plt.subplots(figsize=(8, 4.2))
looks = np.arange(1, K + 1)
ax.bar(looks - 0.15, [1.96] * K, width=0.3, label="Naive z-threshold (1.96)",
       color="#6C371F")
ax.bar(looks + 0.15, boundary, width=0.3, label="O'Brien-Fleming threshold",
       color="#17365D")
ax.set_xticks(looks)
ax.set_xlabel("Look number")
ax.set_ylabel("Critical |z|")
ax.set_title("Repeated looks require a stricter early threshold")
ax.legend()
ax.grid(True, alpha=0.2, axis="y")
plt.tight_layout()
plt.show()
