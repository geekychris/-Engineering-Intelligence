# %% [markdown]
# # Automatic governance classification of a proposed use
#
# Ch 13 and Appendix D. Classify a use proposal against the five-class
# scheme, decide whether it's permitted, and route it to the appropriate
# review body.

# %%
from engintel_utils.governance import (
    UseProposal, UseClass, routing_body, review_cadence,
)

# %%
proposals = [
    UseProposal(
        purpose="Report weekly review-queue latency to the payments team retrospective",
        audience="team", affects_individuals=False, influences_policy=False,
        exposes_sensitive_data=False, reversible=True,
    ),
    UseProposal(
        purpose="Compare deployment reliability across three business units in a CTO report",
        audience="executive", affects_individuals=False, influences_policy=False,
        exposes_sensitive_data=False, reversible=True,
    ),
    UseProposal(
        purpose="Automatically route high-risk changes to specialist reviewer group",
        audience="org", affects_individuals=False, influences_policy=True,
        exposes_sensitive_data=False, reversible=True,
    ),
    UseProposal(
        purpose="Rank engineers on review-latency contribution for promotion decisions",
        audience="executive", affects_individuals=True, influences_policy=True,
        exposes_sensitive_data=True, reversible=False,
    ),
]

# %%
for p in proposals:
    cls = p.classify()
    ok, note = p.is_permitted()
    print("-" * 72)
    print(f"Purpose:   {p.purpose}")
    print(f"Class:     {cls.name}")
    print(f"Routed to: {routing_body(cls)}")
    print(f"Cadence:   {review_cadence(cls)}")
    print(f"Permitted: {'yes' if ok else 'NO'}")
    print(f"Note:      {note}")
