# %% [markdown]
# # Blast radius from a real dependency graph
#
# Ch 9. When you have a service catalogue with real dependencies, the
# reach and exposure components of blast radius aren't guesses — they're
# graph queries.

# %%
from engintel_utils.graph import DAG
from engintel_utils.blast import (
    BlastRadiusScore, blast_reach_from_dag, apply_reversibility,
)

# %%
# Build a small service graph. Arrows point "depends-on" — an arrow
# u -> v means u calls or imports v, so a change in v propagates to u.
g = DAG()
services = [
    "checkout-api", "checkout-worker",
    "payments-api", "identity-api", "identity-cache",
    "auth-library", "audit-log", "notifications-api",
    "customer-portal",
]
for s in services:
    g.add_node(s)

edges = [
    ("checkout-api", "auth-library"),
    ("checkout-worker", "auth-library"),
    ("payments-api", "auth-library"),
    ("identity-api", "auth-library"),
    ("notifications-api", "auth-library"),
    ("identity-cache", "identity-api"),
    ("customer-portal", "checkout-api"),
    ("customer-portal", "payments-api"),
    ("customer-portal", "notifications-api"),
    ("payments-api", "audit-log"),
]
for u, v in edges:
    g.add_edge(u, v)

# %%
# The auth-library change from Ch 9. Which services depend on it?
changed = "auth-library"
customer_facing = {"customer-portal"}
# In this graph, callers are the ancestors of `auth-library`.
callers = g.ancestors(changed)
print(f"Direct + indirect callers of {changed}: {sorted(callers)}")

# %%
# The utility measures descendants; here we want ancestors (things that
# depend on changed). Wrap into a synthetic score.
callers_customer_facing = callers & customer_facing
reach = len(callers) / max(1, len(g.nodes) - 1)
exposure = (len(callers_customer_facing) / max(1, len(customer_facing)))
score = BlastRadiusScore(reach=reach, exposure=exposure, reversibility=0.85)

print(f"Reach:         {score.reach:.2f}")
print(f"Exposure:      {score.exposure:.2f}")
print(f"Reversibility: {score.reversibility:.2f}")
print(f"Composite:     {score.composite():.2f}")

# %% [markdown]
# The auth-library change touches all customer-facing paths and requires a
# coordinated rollback. In our small graph this yields a composite score
# above 0.7 — top-quartile — even though the underlying code diff might
# be trivial. The point of the graph-derived score is to make that
# structural risk visible to the reviewer.
