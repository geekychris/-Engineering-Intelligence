# %% [markdown]
# # Pilot selection scoring
#
# Ch 15. When choosing the first pilot, score candidates against the
# rubric — narrow, consequential, evidence-reachable, sponsored — and
# make the trade-off visible instead of political.

# %%
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np

@dataclass
class PilotCandidate:
    name: str
    sponsor_score: float          # 0-1: strength of an accountable sponsor
    decision_score: float         # 0-1: how consequential the pending decision is
    reachability_score: float     # 0-1: how close the data is
    political_cost_of_failure: float  # 0-1 (higher is worse)
    time_to_first_result_weeks: int

    def rubric(self, w_sponsor=0.30, w_decision=0.30,
               w_reach=0.25, w_political=0.15) -> float:
        return (w_sponsor * self.sponsor_score
                + w_decision * self.decision_score
                + w_reach * self.reachability_score
                - w_political * self.political_cost_of_failure)

candidates = [
    PilotCandidate("Payments reviewer capacity", 0.85, 0.90, 0.75, 0.40, 8),
    PilotCandidate("Whole-company deploy latency", 0.55, 0.50, 0.30, 0.80, 14),
    PilotCandidate("SRE incident quality",       0.70, 0.55, 0.60, 0.25, 10),
    PilotCandidate("AI review evaluation",       0.65, 0.70, 0.60, 0.55, 12),
]

# %%
scores = sorted(candidates, key=lambda c: c.rubric(), reverse=True)
print(f"{'Candidate':40}{'Score':>8}{'Weeks':>8}")
for c in scores:
    print(f"{c.name:40}{c.rubric():+8.2f}{c.time_to_first_result_weeks:>8}")

# %%
# Show the component contributions on a stacked bar so the decision is
# legible to someone who wasn't in the room.
labels = [c.name for c in candidates]
sponsor = [0.30 * c.sponsor_score for c in candidates]
decision = [0.30 * c.decision_score for c in candidates]
reach = [0.25 * c.reachability_score for c in candidates]
political = [-0.15 * c.political_cost_of_failure for c in candidates]

fig, ax = plt.subplots(figsize=(10, 4.5))
x = np.arange(len(labels))
ax.bar(x, sponsor, label="Sponsor",   color="#17365D")
ax.bar(x, decision, bottom=sponsor,  label="Decision at stake", color="#245A88")
ax.bar(x, reach, bottom=np.array(sponsor) + np.array(decision), label="Data reachability", color="#8FC0E8")
ax.bar(x, political, label="Political cost", color="#6C371F")
ax.axhline(0, color="black", linewidth=0.5)
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=15, ha="right")
ax.set_ylabel("Weighted contribution to rubric")
ax.set_title("Pilot selection with component decomposition")
ax.legend(loc="upper right")
plt.tight_layout()
plt.show()
