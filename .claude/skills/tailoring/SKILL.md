---
name: tailoring
description: Per-plan route records, flags that never block, and Charter-first integration-section home for project tailoring (ADR-011): the pure tailoring module in agent_learning.
---

# Tailoring (agent_learning.tailoring)

**Governing:** ADR-011, BRD-011, FDD-011, Epic 11 (Stories 11.1 and 11.2). Contract file: `tests/test_tailoring.py`.

## What it is
A pure functional module (standard library only, no storage, no `pmbok/` import) that models the route chosen for each management plan: `full_plan`, `pmp_section` or `not_applicable`. It runs from a clean install, independent of the PMBOK tooling's dependencies.

## Load-bearing constraints
- **Human decides, system recommends.** A route with `decided=True` needs `decided_by_human=True` and a non-empty `decided_by_role`. A pending recommendation (`decided=False`) is valid.
- **No silent omission.** `validate_route_set()` needs a route for every plan in `PLAN_IDS`, and raises on a missing, duplicate or unknown plan id. `not_applicable` needs a non-blank reason.
- **Both sides recorded.** A decided route needs `recommended_route`, `recommendation_basis` and `rationale`. `to_episode_metadata()` returns a plain dict including `diverged`.
- **Storage boundary.** Routes live in `Episode.metadata`; this module never imports from `agent_learning.storage` (ADR-002 Invariant #2). A contract test enforces it.
- **Flags never block.** `compute_flags()` returns `baseline_plan_omitted` flags (cost, scope, schedule routed `not_applicable`) and never raises for content. A flagged route is still valid; accepting it needs a rationale, like every decided route.
- **Charter prevails.** `resolve_home(charter, pmp, granularity)` puts an integration-section element in the Charter if the Charter defines it, otherwise in the PMP, and reports a conflict when both define it differently. Both granularities exist (`element`, `section`) because ADR-011 leaves the choice open; do not hard-code one. A blank value (`None`, `""`, `[]`, `{}`) does not count as defined.
- **Plan list is one list.** `PLAN_IDS` / `PLAN_NAMES` follow the orchestrator's `PLAN_MAPPING` (6th-edition names). Renaming to the PMBOK 8th-edition terms is deferred and would change this list only.

## Out of scope (see ADR-011)
Plan floors and caps, the Charter template and approval limits, per-plan gates and seam checks, learners, and route-aware generation in `orchestrate_pmbok.py`.

## Call sites
- `agent_learning/__init__.py` re-exports the public names, including `Flag`, `HomeResolution`, `compute_flags` and `resolve_home`.
- No orchestrator or CLI call site yet; route-aware generation is a later epic.
