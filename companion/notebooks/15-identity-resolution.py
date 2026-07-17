# %% [markdown]
# # Identity resolution accuracy — precision, recall, and asymmetric costs
#
# Ch 8. When multiple source identities are merged into canonical actors,
# false positives (wrongly merging two people) are more damaging than
# false negatives. Both metrics matter, but the SLO on precision is
# usually stricter.

# %%
import numpy as np
import matplotlib.pyplot as plt

# %%
# Confusion counts from the Ch 8 worked example
tp = 462   # correctly merged
tn = 21    # correctly kept separate
fp = 8     # wrongly merged (two people collapsed)
fn = 9     # wrongly kept separate (same person as two)

precision = tp / (tp + fp)
recall = tp / (tp + fn)
f1 = 2 * precision * recall / (precision + recall)
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1:        {f1:.4f}")

# %%
# Sensitivity of the composite governance-cost score to the FP/FN mix.
# Governance cost is asymmetric: an FP costs C_fp, an FN costs C_fn.
c_fp_grid = np.linspace(1, 20, 100)  # multiplier for false-positive cost
c_fn = 1.0

# Sweep confidence thresholds. Higher threshold reduces FP but raises FN.
def confusion_at_threshold(t):
    # Toy model: at threshold t, share of TP declines linearly to a floor,
    # while FP declines faster and FN rises.
    tp_t = tp * max(0.60, 1.0 - 0.5 * (t - 0.5))
    fp_t = fp * max(0.05, 1.0 - 3.0 * (t - 0.5))
    fn_t = fn + fp - fp_t
    tn_t = tn + fp_t
    return tp_t, fp_t, fn_t, tn_t

thresholds = np.linspace(0.60, 0.99, 30)
prec_curve = []
rec_curve = []
for t in thresholds:
    tp_t, fp_t, fn_t, _ = confusion_at_threshold(t)
    prec_curve.append(tp_t / max(1e-9, tp_t + fp_t))
    rec_curve.append(tp_t / max(1e-9, tp_t + fn_t))

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(thresholds, prec_curve, label="Precision", color="#17365D", linewidth=2.4)
ax.plot(thresholds, rec_curve, label="Recall", color="#B78331", linewidth=2.4)
ax.axhline(0.99, color="#6C371F", linestyle="--", linewidth=1.0,
           label="Precision SLO (0.99)")
ax.set_xlabel("Confidence threshold for automatic merge")
ax.set_ylabel("Score")
ax.set_title("Precision-recall trade-off along the identity confidence threshold")
ax.legend()
ax.grid(True, alpha=0.2)
plt.tight_layout()
plt.show()

# %%
# Governance-cost surface across FP-cost multiplier and threshold.
best_threshold_by_multiplier = []
for c_fp in c_fp_grid:
    costs = []
    for t in thresholds:
        tp_t, fp_t, fn_t, _ = confusion_at_threshold(t)
        costs.append(c_fp * fp_t + c_fn * fn_t)
    best_threshold_by_multiplier.append(thresholds[int(np.argmin(costs))])

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(c_fp_grid, best_threshold_by_multiplier,
        color="#17365D", linewidth=2.4)
ax.set_xlabel("False-positive cost multiplier vs false-negative cost")
ax.set_ylabel("Cost-optimal confidence threshold")
ax.set_title("As FPs get more expensive, the SLO tightens")
ax.grid(True, alpha=0.2)
plt.tight_layout()
plt.show()
