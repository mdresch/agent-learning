# Epic 11: Project Tailoring and Route Decision

**Source ADR:** [ADR-011](../adr/ADR-011-project-tailoring-and-route-decision.md) — Accepted (2026-10-25)  
**Source BRD/FDD:** [BRD-011](../project-docs/Business-Requirements/BRD-011-project-tailoring-and-route-decision.md) / [FDD-011](../project-docs/Functional-Design/FDD-011-project-tailoring-and-route-decision.md)  
**Status:** Approved (2026-10-25, Menno) — derived from Accepted ADR-011, BRD-011, and FDD-011; adjudicated via `approve-user-stories` (robust utility 0.908, episode `2782c8e3-cbfc-4e62-8cc2-c838ee14a7e7`).  

---

## Story 11.1 — Route Records and the Human-Decision Invariants

**Status:** Ready (2026-10-25)  
**As** a project manager recording planning depth,  
**I want** a validated per-plan route record that captures both the recommendation and my decision,  
**So that** no plan is silently omitted, no route is decided by anything but a human, and the record can be stored as ordinary episode metadata.

### Acceptance Criteria:
- **$AC_0$ (Route Shape):** `PlanRoute` accepts only `full_plan`, `pmp_section` or `not_applicable` as a route; any other value raises `ValueError`.
- **$AC_1$ (No Silent Omission):** `validate_route_set()` raises `ValueError` naming the missing plan ids when any of the nine plans has no route, and raises on a duplicate or unknown plan id.
- **$AC_2$ (Not Applicable Needs a Reason):** a `not_applicable` route with an empty reason raises `ValueError`.
- **$AC_3$ (Human Decides):** a route with `decided=True` raises `ValueError` unless `decided_by_human` is `True` and `decided_by_role` is non-empty. A pending recommendation (`decided=False`) is valid.
- **$AC_4$ (Both Recorded):** a decided route raises `ValueError` unless `recommended_route`, `recommendation_basis` and `rationale` are all set. `to_episode_metadata()` returns the recommended route, decided route, rationale, deciding role and a `diverged` flag.
- **$AC_5$ (Storage Boundary):** `tailoring.py` imports nothing from `agent_learning.storage` and `to_episode_metadata()` returns a plain dict, so no new `LearningStore` record type is introduced (ADR-002 Invariant #2).

---

## Story 11.2 — Flags That Never Block, and Integration-Section Home

**Status:** Ready (2026-10-25)  
**As** a project manager,  
**I want** the system to flag a route that drops cost, scope or schedule and to tell me where each integration-section element lives,  
**So that** I stay the decision-maker with the evidence in front of me, and the Charter-versus-PMP rule is applied the same way every time.

### Acceptance Criteria:
- **$AC_0$ (Baseline-Plan Flag):** `compute_flags()` returns a `baseline_plan_omitted` flag with evidence for each of cost, scope and schedule routed as `not_applicable`, and returns no such flag when each is at least a `pmp_section`.
- **$AC_1$ (Flags Never Block):** `compute_flags()` never raises for content, and a route set that produces flags still passes `validate_route_set()`.
- **$AC_2$ (Accepted Deviation Needs a Rationale):** a decided route that raises a flag raises `ValueError` if its rationale is empty, and is accepted when the rationale is present.
- **$AC_3$ (Charter Prevails):** `resolve_home()` returns `home="charter"` for an element the Charter defines, `"pmp"` for one only the PMP defines, and `None` for neither. When both define an element with different values it returns `conflict=True` and the Charter's value.
- **$AC_4$ (Granularity Stays Open):** `resolve_home(..., granularity="section")` resolves the whole section to the Charter if the Charter defines any element, else to the PMP; `granularity="element"` resolves each element independently. Both modes are covered by tests, so the open question in ADR-011 §7 is not pre-decided.

---

## Out of Scope per ADR-011 / BRD-011 / FDD-011

- Plan floors, caps, the definition of the standard, and breakout triggering.
- The Charter template and its checks, the Project Manager's approval limits and escalation table, and role mapping.
- Per-plan approval gates, seam checks and `approve-pmp`.
- Learners, burden estimation and effort capture.
- Route-aware generation in `orchestrate_pmbok.py`, which needs the PMBOK tooling's dependencies declared and the plan standards defined first.
- Renaming plans to the PMBOK 8th-edition terms.
