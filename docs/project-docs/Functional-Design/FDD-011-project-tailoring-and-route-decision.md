# FDD-011: Project Tailoring and Route Decision

**Source ADR:** [ADR-011](../../adr/ADR-011-project-tailoring-and-route-decision.md) — Accepted (2026-10-25)  
**Source BRD:** [BRD-011](../Business-Requirements/BRD-011-project-tailoring-and-route-decision.md)  
**Status:** Approved (2026-10-25, Menno) — derived from Accepted ADR-011 and BRD-011; adjudicated via `approve-fdd` (robust utility 0.897, episode `21d26da7-e392-4e9b-8072-073c9a0f83d5`).  

---

## 1. Architecture & Component Placement

1. **Module placement:** `src/agent_learning/tailoring.py`, a pure functional module in the same style as `lessons_learned.py`. Standard library only (`dataclasses`, `typing`, `enum`).
2. **Purity boundary:** no file I/O, no storage access, no import of `pmbok/`. Callers pass plain data in and receive plain data or dataclasses out. The module therefore runs from a clean install, independent of the PMBOK tooling's dependencies.
3. **Package export:** the public names are re-exported from `agent_learning/__init__.py`.
4. **Plan identifiers:** one list in the module (`PLAN_IDS`) holds the nine plan identifiers and names, taken from the orchestrator's `PLAN_MAPPING` (5.1 scope, 6.1 schedule, 7.1 cost, 8.1 quality, 9.1 resource, 10.1 communications, 11.1 risk, 12.1 procurement, 13.2 stakeholder). Renaming to the PMBOK 8th-edition terms is deferred and would change this list only.
5. **Baseline-substantiating set:** a constant (`BASELINE_SUBSTANTIATING = {"5.1", "6.1", "7.1"}`: scope, schedule, cost), provisional per ADR-011.

---

## 2. Data Contract & Domain Model

```python
class Route(str, Enum):
    FULL_PLAN = "full_plan"
    PMP_SECTION = "pmp_section"
    NOT_APPLICABLE = "not_applicable"

@dataclass(frozen=True)
class PlanRoute:
    plan_id: str
    route: Route                      # the decided route, or the recommended route if undecided
    reason: str = ""                  # required when route is NOT_APPLICABLE
    recommended_route: Route | None = None
    recommendation_basis: str = ""    # evidence behind the recommendation
    decided: bool = False             # True once a human has decided
    decided_by_role: str = ""         # the deciding role (free text)
    decided_by_human: bool = False    # must be True when decided
    rationale: str = ""               # why the human decided as they did

@dataclass(frozen=True)
class Flag:
    code: str                         # e.g. "baseline_plan_omitted"
    plan_id: str
    message: str
    evidence: str

@dataclass(frozen=True)
class HomeResolution:
    element: str
    home: str | None                  # "charter", "pmp" or None
    value: Any
    conflict: bool
```

`RouteSet` is simply a sequence of `PlanRoute`; there is no separate class.

---

## 3. Functions & Validation Specifications

| Function | Behavior |
|---|---|
| `validate_route_set(routes)` | Raises `ValueError` if any plan in `PLAN_IDS` has no route, if a plan appears twice, if a plan id is unknown, if `NOT_APPLICABLE` has no `reason`, or if a decided route violates the human-decision rules below. Returns the routes unchanged on success. |
| `compute_flags(routes)` | Returns a list of `Flag`. It **never raises** for content and never blocks. Emits `baseline_plan_omitted` for any plan in `BASELINE_SUBSTANTIATING` whose route is `NOT_APPLICABLE`. |
| `resolve_home(charter, pmp, granularity="element")` | Takes two mappings of integration-section elements. Charter prevails. Returns `HomeResolution` entries: `home="charter"` if the Charter defines the element, `"pmp"` if only the PMP does, `None` if neither. `conflict=True` when both define it with different values. With `granularity="section"` the whole section resolves to the Charter if the Charter defines any element, else to the PMP. |
| `to_episode_metadata(route, flags=())` | Returns a plain dict for `Episode.metadata`: recommended route, decided route, rationale, deciding role, `diverged` (decided differs from recommended), and the flag codes. No new record type. |

**Human-decision rules** (used by `validate_route_set`):
- A route with `decided=True` needs `decided_by_human=True` and a non-empty `decided_by_role`; otherwise `ValueError` (BRU-011-02).
- A decided route needs `recommended_route`, `recommendation_basis` and `rationale` all set, so both sides of the pair are recorded (BRU-011-03).
- A decided route that raises a flag needs a non-empty `rationale`; the flag itself never prevents the decision (BRU-011-04).
- A route with `decided=False` is a pending recommendation. It is valid in a set, so a set can be validated while decisions are still outstanding.

---

## 4. Error Handling & Invariants

| Failure condition | Behavior |
|---|---|
| A plan has no route | `ValueError`: names the missing plan ids |
| Duplicate or unknown plan id | `ValueError` |
| `NOT_APPLICABLE` without a reason | `ValueError` |
| Decided route not by a human, or no deciding role | `ValueError` |
| Decided route without recommendation, basis or rationale | `ValueError` |
| Flagged route accepted without a rationale | `ValueError` |
| Route set that triggers flags but is otherwise complete | Valid; flags returned by `compute_flags` |
| Any attempt to persist a route as a new record type | Prohibited by ADR-002 Invariant #2; routes live in `Episode.metadata` |

| ADR-011 invariant | Where it is enforced |
|---|---|
| 1 Human decides | Human-decision rules in `validate_route_set` |
| 2 No silent omission | Missing-plan and `reason` checks in `validate_route_set` |
| 3 Both recorded as `Episode` | `to_episode_metadata` and the decided-route rules |
| 4 Declared by humans, never inferred | Out of this module: nothing here infers a profile or standard |
| 5 One home, Charter prevails | `resolve_home` |

---

## 5. Deferred to Other Designs
Floors, caps and the standard's definition; Charter parsing and template; approval limits and the escalation table; breakout triggering; route-aware generation in `orchestrate_pmbok.py`; learners; and effort capture.
