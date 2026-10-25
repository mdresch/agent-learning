# BRD-011: Project Tailoring and Route Decision

**Source ADR:** [ADR-011](../../adr/ADR-011-project-tailoring-and-route-decision.md) — Accepted (2026-10-25)  
**Governing Baseline:** none approved yet (`approve-pmp` is not built; see ADR-011 §2)  
**Status:** Approved (2026-10-25, Menno) — derived from Accepted ADR-011; adjudicated via `approve-brd` (robust utility 0.878, episode `c460e297-f949-4261-8306-cc9e618f93e8`).  
**Stakeholders:** Menno (Sponsor/PM/maintainer)  

## Business Need

The PMBOK tooling generates all nine management plans for every project, whatever its size or resources. ADR-011 decides that planning depth is chosen per management plan, that a human decides and the system only recommends, and that every choice is recorded. This BRD turns that decision into the smallest set of business rules that can be built and tested now. The wider design (Charter contents, approval limits, ownership, learners, plan floors and caps) is not decided and is out of scope here.

## Business Rules (BRU)

- **BRU-011-01 (A Route per Plan):** Every management plan has a recorded route: a full plan, a PMP section, or not applicable with a stated reason. A route set that omits a plan, or marks a plan not applicable without a reason, is invalid. Omission is never silent (ADR-011 Invariant 2).
- **BRU-011-02 (Human Decides):** A route is decided by a human. The system may recommend a route but may not decide it. A decision attributed to anything other than a human is rejected (ADR-011 Invariant 1).
- **BRU-011-03 (Recommendation and Decision Both Recorded):** Every decided route records both what was recommended and what was decided, with the rationale and the deciding role. Whether the decision departed from the recommendation is derivable from the record (ADR-011 Invariant 3).
- **BRU-011-04 (Flags, Not Blocks):** A route that omits cost, scope or schedule (the plans that substantiate the PMP's baselines) is flagged with evidence. A flag never prevents a decision. Accepting a flagged route requires a recorded rationale (ADR-011 Decision 2).
- **BRU-011-05 (One Home for the Integration Section):** An element of the integration section (type, route per plan, owners) has one home at a time: the Charter if the Charter defines it, otherwise the PMP. If both define the same element, the Charter prevails and the conflict is reported (ADR-011 Invariant 5).
- **BRU-011-06 (Storage Boundary):** Route records are stored only as metadata on standard `Episode` records. Zero new `LearningStore` record types (ADR-002 Invariant #2; ADR-011 Invariant 3).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Route coverage | 100% of route sets accepted by the validator contain a route for every plan |
| Silent omissions | 0 accepted route sets with an omitted plan or an unexplained "not applicable" |
| Human decisions | 0 decided routes attributed to a non-human decider |
| Recorded pairs | 100% of decided routes carry both recommendation and decision with a rationale |
| Flag integrity | 0 decisions blocked by a flag; 100% of accepted flagged routes carry a rationale |
| Storage boundary | 0 new record types added to `LearningStore` |

## Out of Scope

- Plan floors, caps, the definition of the project standard, and the foundation-breakout mechanics (plan standards ADR).
- The Charter's contents and template, the Project Manager's approval limits, the escalation table, and role mapping (a later Charter ADR).
- Per-plan approval gates, seam checks and `approve-pmp` itself (decision gates ADR).
- Learners, burden estimation and the 300K / 12% figures (learner ADR and working notes).
- Route-aware generation in `orchestrate_pmbok.py`: the orchestrator cannot run from a clean install until its dependencies are declared, and PMP-section content depends on the plan standards.
- Renaming plans to the PMBOK 8th-edition terms.
