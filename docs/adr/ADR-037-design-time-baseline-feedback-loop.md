# ADR 037: Design-Time Baseline Feedback Loop (Stage 7-8 → Stage 16 → Stage 6)

## 1. Executive Brief
The approved baseline (Stage 6) has one route back today: Stage 16 (Governance Change) → Stage 17 (Adaptation Plan) → Stage 6 (ADR-008 §4.4). That route assumes the trigger is evidence from executed work: deliverables, tests, audits, observed outcomes, insights and lessons learned (Stages 9-15). Writing and reviewing Stage 7 requirements, or checking Stage 8 readiness, can find defects in the approved baseline *before anything is built*. The chain has nowhere to put them, so they get forced into an Adaptation Plan, which is the wrong stage, invites schedule numbers that have no duration data behind them, blocks Phase 1 work on an adaptation that cannot legitimately exist yet, and asks the approver to approve an amendment instead of a baseline.

This ADR decides a second, **design-time** route from Stages 7-8 back to the baseline, alongside the execution route and not replacing it:
1. Each finding is captured as a `BFI-NNN` (baseline feedback item) that cites the documents involved.
2. It is classified and routed by the **existing** Stage 16 policies (`classify-diff-type`, `escalate-diff-response`), with the evidence marked `design_time`.
3. What the approver sees is a complete revised baseline (a **Baseline Revision Package**), never an amendment.
4. The route fixes logic and records variance only. It is never a lesson learned, never uses Stage 17, and never refines Intent (Stage 18).

It adds no `TaskPolicy`, no `LearningStore` record type (ADR-002 Invariant #2) and no autonomy (ADR-001, ADR-003).

---

## 2. Status
**Accepted (2026-10-27, Menno)** — Cross-cutting. Episode: `0eb8f52a-dea7-4ef6-8ac5-0e0e21def933`.

The loop was adopted on 2026-10-27 in the sibling project Kayros Bay (its PROP-001) and the SIDPA template was updated to match (sidpa-template branch `feat/baseline-feedback-loop`, commit `9264e16`, not pushed). That adoption is the maintainer's report; it is not independently verified in this repository.

---

## 3. Context & Problem Statement
- **One route back (verified).** ADR-008 §4.4 draws the feedback cycle as Stage 16 → Stage 17 → subsidiary plans → Stage 6 → Stage 7. ADR-007 §4.5 ends Stage 16 at "a formally validated, immutable governance baseline" and leaves everything after it to Stage 17. Nothing connects Stage 7 or 8 to Stage 6 directly.
- **The Adaptation Plan is built from accepted Stage 16 amendments (verified).** ADR-008 §4.5 defines the Governance Change Impact Matrix that an Adaptation Plan fills, and §4.4 places the lessons-learned stages (14-15) as what feeds Stage 16. Nothing in either lets a finding that precedes Stage 9 take that path honestly.
- **Baseline versioning has no row for it (verified).** ADR-008 §4.6.1 defines `PMP-BL-v1.0.0` (initial), `PMP-BL-v1.1.0` (adaptive iteration, "minor for scope/quality/risk tailoring") and `PMP-BL-v2.0.0` (charter restructuring). A design-time fix is none of these.
- **The case that surfaced it (reported, not verified here).** In Kayros Bay, writing Stage 7 requirements and checking Stage 8 readiness found: an approved critical path that contradicted the directive that the Blueprint comes first, a circular PoC gate and a lapsed milestone (AMD-001); accepted ADRs that implied plan updates the plans lacked (AMD-002); ADRs that conflicted with each other and with the Brand Manual (AMD-003). With no design-time route they went into the Adaptation Plan. AMD-001 claimed Stage 17 status with no Stage 9-15 evidence and skipped the Stage 16 classification its own gate required; attached a new 99-day critical path to a logic fix (a schedule with no real duration data); left Phase 1 stories blocked on an adaptation that could not yet exist; and would have asked the Steering Committee to approve an amendment instead of a revised baseline.
- **The pieces to reuse exist.** `classify-diff-type` (7 classes, `full` authority) and `escalate-diff-response` (3 actions, `low` authority) are built (ADR-007; `agent_learning.governance.evaluate_governance_diff`). Plan re-approval after a change and bounded staleness are specified (ADR-013 §4.5, §4.7). `Episode.metadata` is free-form.

---

## 4. Technical Decision

### 4.1 Two routes back to the baseline, disjoint by evidence
| Route | Trigger | Path | Baseline increment |
|---|---|---|---|
| **Execution** (unchanged, ADR-008 §4.4) | Evidence from executed work: Stages 9-15 | Stage 16 → Stage 17 → Stage 6 | minor (`PMP-BL-v1.1.0`) |
| **Design-time** (this ADR) | A baseline defect found while writing or reviewing Stage 7, or checking Stage 8 readiness, cited to documents | Stage 7-8 → BFI → Stage 16 → Stage 6 | patch (`PMP-BL-v1.0.x`) |

A finding enters exactly one route. A finding that needs executed-work evidence to be true is not a design-time finding.

### 4.2 Capture: the BFI
A baseline defect found at Stage 7 or 8 is logged as `BFI-NNN` with: where it was raised (stage and document), the finding citing the documents directly (file and section), its classification, its route and its status. BFIs live in a **Pending Baseline Feedback** table in the PMP (an internal working item, not a new record type). "None" is a valid entry. A Stage 7 document does not fix the baseline inside itself: it raises the BFI and cites it (ADR, BRD, FDD and Epic templates carry a "Baseline Feedback (Stage 7-8 → 6)" section; a story blocked by an open BFI names it in its Status line).

### 4.3 Classify and route with the existing Stage 16 policies
The finding is classified by `classify-diff-type` and routed by `escalate-diff-response`, both unchanged. The result lands in one of four places:
- **Editorial:** apply and log.
- **Upstream ADR / BRD / FDD:** amend it, then re-confirm it with its own `approve-*` policy (the ADR-007 classes apply to the amendment).
- **Within PM authority:** the PM revises the plan and the plan's own policy re-approves it; plans that were not regenerated keep their approvals (ADR-013 §4.7).
- **Steering-Committee level:** the PM produces a Baseline Revision Package (§4.4).

The thresholds that separate these four come from the approval limits declared in the Charter, not from this ADR. In this repository the sponsor, PM and maintainer is one person (Menno), who holds every level.

### 4.4 Submit a baseline, not an amendment
For a Steering-Committee-level item the unit of approval is a complete revised baseline, the **Baseline Revision Package**:
- **Always:** the revised PMP and the changed plans, plus the standard set (Spark, Ideation, Business Case, Benefits Statement, Stakeholder Register).
- **Only if amended:** the Charter.

`approve-pmp` records the new baseline. The previous baseline is archived as in ADR-008 §4.6.2.

### 4.5 Guardrails
- The route fixes logic and records variance only. It adds no new durations, costs or estimated dates, because no real duration or cost data exists before work is done (progressive elaboration: ADR-026, ADR-027).
- It invents no evidence. A BFI cites documents that exist.
- Human approval throughout: the `approve-*` gates stay human-held (ADR-001), and the classes that alter lineage stay frozen from autonomy (ADR-007 Invariant #4).

### 4.6 Separation from the execution loop
A design-time fix is never a lesson learned (ADR-010), never touches Stage 17 (ADR-007 §4.5 is unchanged for execution) and never refines Intent (Stage 18, ADR-009). The execution loop's inputs stay execution evidence.

### 4.7 No new TaskPolicy
The existing pair fits. A new policy would need repeated, evidenced cases of a judgment the pair cannot make; none exists.

### 4.8 Cascade back
After a change is applied, the downstream Stage 7 documents are re-checked and the chain is re-entered where the finding was raised. Plans that changed lose their approval and are re-approved; staleness follows the dependency DAG and no further (ADR-013 §4.5).

### 4.9 Versioning
Design-time revisions are patch increments (`PMP-BL-v1.0.x`). Minor increments (`PMP-BL-v1.1.0`) stay reserved for Stage 17 adaptations from executed work. This extends ADR-008 §4.6.1 with one row; archival and traceability tagging (§4.6.2, §4.6.3) are unchanged.

### 4.10 Evidence separation in episodes
Change-control episodes carry `evidence_basis: design_time | execution`. `evaluate_governance_diff` takes an optional `evidence_basis` (closed list, default `execution`, so existing callers are unchanged) and writes it into the `audit_evidence` envelope and the audit episode metadata. It is not a feature of the low-authority bandit (ADR-006 non-interpretation); it exists so that any later learning from these episodes does not mix the two kinds of evidence. The code change follows this ADR's acceptance as its own BRD, FDD and Epic.

**Gate until then.** The route is specified here and is gated, in code, on that story. Until the parameter exists, `evaluate_governance_diff` must not be used for a design-time BFI: it records no `evidence_basis`, and an episode without the key reads as `execution`. A design-time finding is classified instead through the policy CLI (`task-policy-decide`, `task-episode-register`) with `evidence_basis: design_time` written into the episode metadata by the caller.

### 4.11 Plan and template standard
- The PMP's feedback section names both loops and carries the Pending Baseline Feedback table. The PMP is produced by tooling and is not hand-edited: the standard belongs in the generator. The legacy generator is being decommissioned (ADR-034), so the ported PMP builder must emit it; this ADR does not change the legacy generator.
- The SIDPA template carries the matching changes (chain coverage §3.1, Rule #21, PMP template §3, and the four spec templates).

### 4.12 What This Does Not Decide
- Who the "Steering Committee" is in a given project (it is whoever the Charter's approval limits name).
- Any duration, cost or date for a revised baseline.
- Retroactive re-classification of past Adaptation Plans.
- The `BFI` id scheme across cycles (§8).

---

## 5. Architectural Invariants
1. **Two disjoint routes.** A finding enters the design-time route or the execution route, by its evidence, never both.
2. **A baseline, not an amendment.** The Steering-Committee-level unit of approval is a complete revised baseline.
3. **No numbers without data.** The design-time route adds no durations, costs or estimated dates and invents no evidence.
4. **Human approval throughout.** No design-time change is applied by an autonomous policy beyond what ADR-007 already permits for editorial classes.
5. **Zero storage sprawl.** No new `LearningStore` record type (ADR-002 Invariant #2): the BFI is a PMP table row; the decision is an `Episode` with free-form metadata.
6. **No new TaskPolicy** while the existing pair fits.
7. **Patch for design-time, minor for execution.** Baseline increments are not interchangeable.

---

## 6. Alternatives Considered
| Alternative | Reason for rejection |
|---|---|
| Keep sending Stage 7-8 findings through the Adaptation Plan | The reported case shows the failure: wrong stage, no Stage 9-15 evidence, a schedule with no duration data, false blockers, an amendment as the unit of approval. |
| Add a new TaskPolicy for baseline findings | The existing classify/escalate pair already separates editorial, upstream, PM and Steering-level changes. A policy is built only after a judgment repeats and the existing ones cannot make it. |
| Record them as lessons learned | Lessons crystallize from implementation (ADR-010) and feed Stage 17 and Stage 18. A baseline logic defect found before building is not one. |
| Allow Stage 17 with an `evidence_basis` flag | Stage 17's defining input is a validated Stage 16 change from executed work (ADR-008 §4.5). Relaxing it blurs the two routes and the minor/patch versioning. |
| Only add rows to ADR-007 and ADR-008 | The change also touches baseline versioning, the PMP standard and the spec templates. Both ADRs get an Amendment Log pointer; the decision itself is one document. |

---

## 7. Consequences
### Positive
- Stage 7-8 findings have a defined, human-approved home; the Adaptation Plan keeps its meaning.
- The approver sees a baseline, so a decision means "this is the plan now", not "this patch is fine".
- Design-time and execution evidence stay separable for later learning.
- No new policy, no new storage, one optional parameter in code.

### Negative
- More bookkeeping before building: BFIs, a package, a cascade check.
- The line between "design-time" and "execution" depends on the finding citing documents rather than results. A finding that is really execution evidence could be labelled design-time to avoid Stage 17's evidence requirement; the citation rule and human approval are the only guard.
- The Steering Committee is a role; in a one-person project it adds a ceremony without a second pair of eyes.
- Until the ADR-034 port exists, the generated PMP in this repository does not carry the new section.

---

## 8. Open Questions & Future Extensions
1. **BFI ids across cycles.** Should `BFI-NNN` be unique per `cycle_id` (ADR-035) or per baseline?
2. **ADR-013 interaction.** A patch baseline re-approves changed plans and propagates staleness down the DAG; is a patch `PMP-BL-v1.0.x` recorded when one plan changes within PM authority, or only for Steering-level packages?
3. **Thresholds in this repository.** The Charter's approval limits are not yet declared here; until they are, every level is Menno.
4. **Retro-logging.** Whether past design-time findings that went into Adaptation Plans (in any project) are re-logged as closed BFIs.
5. **Code story.** The `evidence_basis` parameter on `evaluate_governance_diff` (BRD, FDD and Epic after acceptance).

---

## 9. Amendment Log
| Date | Change | Why |
|---|---|---|
| 2026-10-27 | Proposed | The maintainer adopted a design-time baseline feedback loop in Kayros Bay (PROP-001) after Stage 7-8 findings were forced into an Adaptation Plan, and asked for the governance model and the SIDPA template to carry it. Drafted against ADR-007, ADR-008, ADR-013 and the code. |
| 2026-10-27 | **Accepted by Menno** | Formally adjudicated and accepted through `approve-adr`; robust utility 0.749, expected utility 0.818; Episode `0eb8f52a-dea7-4ef6-8ac5-0e0e21def933`. |
