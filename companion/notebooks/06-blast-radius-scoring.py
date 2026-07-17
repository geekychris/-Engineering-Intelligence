# %% [markdown]
# # Blast-radius scoring
#
# Reproduces the Ch 9 worked example: a shared-authentication library
# change that looks small (38 LOC, one repo) but scores in the top
# quartile of blast radius once reach, exposure, and reversibility are
# considered.

# %%
from dataclasses import dataclass
from typing import Iterable
import matplotlib.pyplot as plt
import numpy as np

@dataclass
class ChangeBlastRadius:
    reach: float           # fraction of downstream units immediately affected [0,1]
    exposure: float        # fraction of affected units that face external users [0,1]
    reversibility: float   # difficulty of rollback [0,1] (0 = trivial, 1 = requires full-fleet redeploy)

    def score(self, w_reach=0.4, w_exposure=0.3, w_rev=0.3) -> float:
        return (w_reach * self.reach
                + w_exposure * self.exposure
                + w_rev * self.reversibility)

# %%
# Ch 9 worked example.
downstream_services = 47
immediate_uptake = 31
customer_facing = 5

case = ChangeBlastRadius(
    reach=immediate_uptake / downstream_services,
    exposure=customer_facing / downstream_services,
    reversibility=0.85,   # session-cookie change; coordinated rollback
)
print(f"Reach:         {case.reach:.2f}  ({immediate_uptake}/{downstream_services} services)")
print(f"Exposure:      {case.exposure:.2f}  ({customer_facing}/{downstream_services} customer-facing)")
print(f"Reversibility: {case.reversibility:.2f}")
print(f"Blast radius:  {case.score():.2f}  ({'top quartile' if case.score() >= 0.5 else 'lower quartiles'})")

# %%
# Compare against a corpus of other hypothetical changes to see the score
# in context. Values chosen to represent a plausible mix.
corpus = [
    ("typo in README", ChangeBlastRadius(0.02, 0.00, 0.05)),
    ("bug fix in one leaf service", ChangeBlastRadius(0.02, 0.00, 0.20)),
    ("new feature behind flag", ChangeBlastRadius(0.10, 0.02, 0.30)),
    ("cross-team API addition", ChangeBlastRadius(0.30, 0.20, 0.55)),
    ("shared-config change", ChangeBlastRadius(0.55, 0.30, 0.70)),
    ("shared-auth session refresh", case),
    ("infra migration", ChangeBlastRadius(0.80, 0.50, 0.90)),
]
labels = [name for name, _ in corpus]
scores = [c.score() for _, c in corpus]

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.barh(labels, scores, color="#17365D")
for i, s in enumerate(scores):
    ax.text(s + 0.01, i, f"{s:.2f}", va="center", color="#17365D")
ax.axvline(0.5, color="#B78331", linestyle="--", linewidth=1.4,
           label="Top-quartile boundary")
ax.set_xlim(0, 1.0)
ax.set_xlabel("Blast radius score")
ax.set_title("Where the shared-auth change sits in the distribution")
ax.legend(loc="lower right")
ax.grid(True, alpha=0.2, axis="x")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Interpretation
#
# The 38-line change scores 0.76 — well into the top quartile — and would
# fire the coordinated-rollout playbook, specialist review, and rollback
# rehearsal that its pull-request diff never triggers. The point of the
# score is to set the process, not to block the change.
