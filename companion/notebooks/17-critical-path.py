# %% [markdown]
# # Multi-repository critical path
#
# Ch 9. When an Engineering Change spans several repositories with
# ordering constraints, its elapsed time is the longest path through
# the dependency DAG — not the sum of the components.

# %%
from engintel_utils.graph import DAG, critical_path, parallelism_ratio

# %%
# Model a payments migration with dual-write, backfill, cutover, retire.
g = DAG()
tasks = {
    "spec": 2.0,             # days of effort
    "dual_write_impl": 8.0,
    "backfill_impl": 5.0,
    "read_cutover_impl": 4.0,
    "retire_legacy": 3.0,
    "monitoring_impl": 4.0,
    "docs": 2.0,
}
for t in tasks:
    g.add_node(t)

# Ordering constraints
g.add_edge("spec", "dual_write_impl")
g.add_edge("spec", "monitoring_impl")
g.add_edge("dual_write_impl", "backfill_impl")
g.add_edge("backfill_impl", "read_cutover_impl")
g.add_edge("read_cutover_impl", "retire_legacy")
g.add_edge("spec", "docs")
g.add_edge("monitoring_impl", "read_cutover_impl")

path, total_days = critical_path(g, tasks)
p_ratio = parallelism_ratio(g, tasks)

print(f"Total work: {sum(tasks.values()):.1f} engineer-days")
print(f"Critical path duration: {total_days:.1f} days")
print(f"Parallelism ratio: {p_ratio:.2f}")
print("Critical path:")
for t in path:
    print(f"  → {t}  ({tasks[t]:.1f} days)")

# %% [markdown]
# The critical path here is longer than any individual component. Adding
# engineers to `docs` or `monitoring_impl` doesn't shorten it. Reducing
# `backfill_impl` or `read_cutover_impl` does. The graph makes this
# explicit; a flat task list would hide it.
