# Planning redesign: working notes (not decided)

**Status:** working notes, not an ADR. Nothing here is accepted or binding. It holds the full draft that preceded the light ADR-011, kept so no confirmed detail is lost. Items move into a small ADR only once they have hardened through use or repeated confirmation.

**Fixes from the third review, to apply when these items harden:** (A) lowering a baseline-substantiating plan below a section is *strongly flagged*, not forbidden (the draft below says "can lower only to a section" in the lowering-depth bullet); (B) use "PMP section" throughout, a section being one or more paragraphs; (C) for a research-only stage, no management-envelope comparison is applied (effort units); open question: does the next stage compare against the proposed envelope, marked "proposed, not yet approved"; (D) "Project Manager" and "the approver the Charter names" are functional anchors, and mapping them to organizational roles is deferred.

---

## Full draft, formerly ADR-011: Project Tailoring and Route Decision — How Much Planning a Project Needs

## 1. Executive Brief
The PMBOK tooling generates all nine subsidiary management plans for every project, whatever its type, size or resources. Following the standards in full carries a management burden that does not depend on the project. A practitioner estimate (Menno, from experience; **unverified, not measured**) puts that burden for a full suite at around 300K. At the conventional 12% management fee, that burden is proportionate to a project of about 2.5M (300,000 ÷ 0.12). For a smaller project the same ceremony is out of proportion. The Ideation Document already declined to fill the PMBOK sub-sections for `agent-learning` itself on exactly this ground ("not a staffed, budgeted project", naming the mismatch rather than "forcing irrelevant ceremony").

This ADR decides **how the amount of planning is chosen and who decides it**:
- A **route** is recorded for each management plan: a full plan, a section inside the PMP, or not applicable with a stated reason. A first cycle of "PMP only" is a valid route.
- **The system recommends and records; the project team decides.** Floors, caps and expectations are flags in front of a human, not blocks. The PMP holds the decision and its human approval.
- The **Project Charter** sets the limits: a minimum baseline, the Project Manager's approval limits and the conditions for further approval, the funding stage, the project profile and the project-level standard. The **integration section** forms the decision (type, route, owners) within them. It lives in the Charter if the Charter defines it, and otherwise in the PMP.
- A PMP section that does not meet its standard, or outgrows it, triggers a **foundation breakout** for that plan. A sufficient paragraph needs none.
- Later changes to depth go back through **Stage 17 to the plan foundation**; changes to the standard go through **Stage 18 back to Intent**, damped against noise.

## 2. Status
**Proposed (2026-10-25)** — drafted for review and consolidated after review feedback. Not yet evaluated through the `approve-adr` TaskPolicy and not yet accepted by Menno Drescher. No robust utility or episode ID exists for this ADR. Items marked *provisional* are defaults awaiting confirmation (§9). The specific roles (sponsor, PMO, project manager, committees, other stakeholders) are deliberately deferred (§4.13).

## 3. Context
- **The tooling has no route concept.** `scripts/orchestrate_pmbok.py` sets `target_processes = list(PLAN_MAPPING.keys())` in `--mode full`, so all nine plans are always generated. `--mode adapt` narrows that to the plans ticked in `Adaptation-Plan.md`, which is the only existing way to vary the set.
- **Size already mattered once.** Ideation Document §4.2–4.9 left the PMBOK knowledge-area, WBS, schedule, cost, HR, procurement and change-management sections unpopulated, naming "a scope mismatch, not silently skipped".
- **Complexity is declared, not inferred.** ADR-003 §4.1 makes a complexity profile governance-controlled metadata set by a human; §5 rejects inferring complexity from the agent's own output and rejects automatic reclassification from outcome history, because a self-grading agent has an incentive to understate effort. `docs/policy-shapes/shared-complexity-profile.json` carries the declared dimensions.
- **The PMP gate keys off the profile and stays manual.** ADR-008 §4.8 selects `approve-pmp` weighting profiles from the complexity profile; ADR-008 Invariant #4 makes human sign-off on `approve-pmp` permanent. `approve-pmp` itself is designed but **not built**: only an action shape and an example decision frame exist, and no decision episode is recorded.
- **BRU-008-04 is an intent, not a check.** It requires the PMP to be re-synthesized "to ensure global baseline consistency" across scope, schedule, cost, quality and risk. No consistency check is implemented in the orchestrator.
- **The chain assigns tailoring to Stage 17.** The coverage matrix row for Stage 17 reads "4.6 Perform Integrated Change Control (Tailoring)", and Stage 18 feeds back to Stage 1. ADR-009 §4.10–4.11 provide damping and rate-limiting against strategic whiplash.
- **The Charter already shows the shape wanted.** `Project-Charter.md` has In/Out of Scope, Resource Requirements, Milestones and Constraints, and a time-boxed research phase (M0.5, 40 hours) with a Go/No-Go rule written before it started, plus a resourcing gate before Phase 2. It has no profile or standard section, covers human resources only, and is scoped to Phase 1.
- **Real Charter examples** (ADPA-generated sections shared by Menno) show a per-transaction approval limit with an escalation target, several escalation bodies depending on the trigger, and the difference between approving and being notified. They also show weaknesses: a placeholder total budget, no cumulative cap, undefined thresholds ("budget or risk thresholds", "major milestones") and no response times.
- **PMBOK 8th edition** (licensed copy, paraphrased, section numbers only). The 6th-edition integration processes map to the Governance domain: Initiate Project or Phase (2.1.6.1) and Integrate and Align Project Plans (2.1.6.2). There is no separate "integration management plan"; the PMP is the output and may be documented as a governance plan or similar. Integrate and Align Project Plans should, at the start, establish tailoring considerations and the development approach and life cycle, and planning should be sufficient but not more detailed than necessary. Customizing governance is typically part of Initiate Project or Phase but may recur, and tailoring outcomes may be recorded in the PMP, another document or a system of record (2.1.7). Section 3 describes tailoring as add, modify, remove, blend or align, using a non-rigid suitability filter, with PM approval usually enough for internal tailoring and PMO approval for tailoring that affects external groups, and as iterative (3.2–3.4). Table 3-1 suggests authorizing decision-makers up to value thresholds. The edition has seven performance domains, not ten knowledge areas; the repository's "PMBOK 8" numbering follows the 6th edition (§9).
- **The three-part model** (Potential, Ambition, Performance) comes from Menno's own articles as conceptual formulas: Potential = (S × L) · B · H^t, Ambition = (V × D) · (C / F) · E^t, Performance = (Pr × F) · C · (St / Fr)^t. They are **not calibrated against data**.
- **Burden figures are a practitioner's recollection.** ~300K and 12% are not measured in this repository.

## 4. Decision

### 4.1 A route per management plan (*provisional depths*)
Every management plan has a recorded route, decided **per plan**, not as one depth for the project:
- **Full plan:** its own document, with a foundation breakout, a template-governed draft and a plan approval.
- **PMP section:** a section inside the PMP that meets the plan's floor (§4.2).
- **Not applicable:** only with a stated reason.

The absence of a plan is always a recorded decision, never a silent omission. A first cycle in which the plans are PMP sections or not applicable ("PMP only") is a valid route.

### 4.2 Floors, caps and expectations are flags; the team decides
The plan standards (a later ADR) define, per plan, the **floor** (the minimum a PMP section and a full plan must contain) and a **cap** (the most a PMP section may carry). The project's standard (§4.5) may raise the bar above the floor.

A route or content that falls below a floor, exceeds a cap, or sets "not applicable" on a baseline-substantiating plan (§4.3) is **flagged**, with the evidence and a recommendation. It is **not blocked**. The project team decides, the PMP holds the decision, and the human approval of the PMP accepts or rejects it. Both **what the system recommended** and **what the team decided**, with the rationale, are recorded, and the difference is itself evidence. Where an organizational policy or contract mandates a minimum, the flag says so and a deviation needs the approver the Charter names for that case. "No silent omission" remains absolute, because it concerns recording.

### 4.3 Baseline-substantiating plans, the baseline, and graduation
- **The baseline to work to** is formed from scope (including explicit out-of-scope items), schedule and resources.
- **Baseline-substantiating plans** are **cost, scope and schedule** (confirmed by Menno as the strong candidates; *provisional*). The cost plan gives a clear overview of costs and is often needed earlier than the others to substantiate the PMP. They are expected to be at least a PMP section that substantiates the baseline. "Not applicable" is a strongly flagged deviation (§4.2). A scope section states what is out of scope as well as what is in.
- **The PMP integrates and points to detail.** It must not turn into a long treatise on cost, scope or schedule.
- **Graduation.** When substantiating a baseline would need more than a section's cap (for example several chapters on cost), the section is **flagged to graduate** to its designated management plan: a full plan with a foundation breakout, a draft against the template and a plan approval, while the PMP section shrinks to a summary and a link. The human decides whether to graduate; nothing forces it and no expiry is imposed on a section the team chooses to keep. The decision is recorded with its rationale.

### 4.4 What triggers the foundation route
Foundation breakouts are remedial and evidence-triggered for plans kept as PMP sections:
1. **A full-plan route chosen at the route decision** starts with its breakout.
2. **A PMP paragraph that fails its standard** triggers a breakout to find the foundation for that paragraph, after which the paragraph is regenerated.
3. **A PMP paragraph that outgrows its cap** graduates (§4.3).

A sufficient paragraph needs no foundation route. PMP validation looks at each paragraph a plan brings in, so a finding names the paragraph and therefore the plan. Plan approvals apply to full plans; paragraphs are validated as part of PMP validation. The approval gates and seam checks are the gates ADR's subject (§4.13).

### 4.5 The Project Charter: minimum baseline, limits, stages and standard
The Charter always carries:
1. **A minimum scope and baseline** for the research stage or the project: in scope and out of scope, the resources and funding authorized now, and the time-box or schedule.
2. **The Project Manager's approval limits, and when further approval is required.** What the Project Manager may approve alone, with measurable limits (per transaction, cumulative, per period), and the conditions that require the approver the Charter names: each trigger with its threshold, the named approver or body, whether it is approve or notify, and a response time. Required triggers include budget, schedule and milestones (with "major" defined), scope baseline, risk thresholds, compliance and security, and, from this ADR, route changes, graduation, and any change in funding requirements.
3. **The size the company allows** the project to launch at (a ceiling; exceeding it is a flag, §4.2).
4. **The project profile and the project-level standard.** The profile covers type, size, resources, complexity (the ADR-003 dimensions), and the attribute groups PMBOK 8 §3.4.3 names for the product, the team and the culture, with Potential, Ambition and Performance as the lens (§4.8). The standard is the bar the project sets for itself, at project level, and is reviewed each cycle (§4.10).
5. **Staged funding.** If the Charter permits research funding, it states that stage's allocation, time-box and disposition rule, written before the stage starts. **The PMP's first review states only the research funding; a change in funding requirements can be indicated only after the foundational work for the cost plan is done.**

All of it is declared by humans and never inferred, reclassified or improved by an agent from outcomes (ADR-003 §4.1). The sponsor confirms the complexity and the resource requirements across departments. A Charter that lacks the minimum is flagged for its approver.

### 4.6 The integration section: one home, the Charter first
The integration section holds the **project type, the route per plan and the distribution to owners** (drawn from the stakeholder register). It is formed after the Business Case, the Benefits Management Plan, the initial Stakeholder Register and the Charter, and before the subsidiary content is drafted.
- **Its home is the Charter if the Charter defines it; otherwise the PMP.** It is never held in two places. If both define the same element, the Charter prevails and the PMP version is flagged. Whether the rule applies to the whole section or per element is open (§9).
- **The home decides who approves a change:** a Charter amendment is approved as the Charter requires, a PMP change by the Project Manager. A Charter amendment can later absorb a section held in the PMP.
- **No new TaskPolicy.** The decision is approved through the existing gates: `approve-charter` when the section is in the Charter, `approve-pmp` when it is in the PMP (*provisional*). The system's route recommendation is advisory tooling output.
- **The approved route is recorded as an `Episode`** (ADR-002) and mirrored in the Charter or PMP section that holds it.
- **Ordering within planning:** integration decision, then drafting according to the route, then paragraph validation and any plan approvals, then PMP formalization and approval. The 18 stages are not subdivided.

### 4.7 Who approves what (role-neutral)
- **The Project Manager approves the PMP.** This is the permanent human approval of ADR-008 Invariant #4.
- **A new PMP, or a Charter change, that introduces new floor amounts also needs the approvers the Charter names** (referred to here as the sponsors). **The Project Manager signals that the amounts have changed and what the Charter requires for approval.** A PMP that stays inside the Charter's amounts needs only the Project Manager.
- **Inside the Charter's limits the Project Manager decides** route changes, graduations and deviations; **beyond the limits, or on a named trigger, the Charter's named approver decides.** Whether a trigger means approval or only notification is stated in the Charter.
- A decision with several approvers is one `Episode` with the approvers listed in its metadata; how the sign-offs are captured is an FDD matter.
- The specific roles are deferred (§4.13).

### 4.8 The recommendation: evidence split and the three-part model
- **The system supplies measured facts only:** for example gate outcomes, suite results, rework, friction signals (Performance), and evidence of shipped work.
- **The human supplies judgments, each with a recorded rationale:** vision, drive, appetite for risk, opportunity, potential, and the standard.
- **The formulas structure the recommendation; they are not computed.** No product of invented scores is calculated. The model contributes its terms as criteria groups, a **weakest-term cap** (the formulas are multiplicative, so one low factor limits the whole), and **misalignment flags**: Potential without Ambition drifts and disperses, Ambition without Potential burns fast, and Performance without both is inconsistent luck.
- **Standard sustainability.** A high standard against measured high friction is flagged as unsustainable.
- **A number is introduced for a term only when that term has a defined, measurable indicator.**
- **More budget, more uncertainty to remove.** As the budget at stake rises, the route must retire more uncertainty. A route that leaves risk and its supporting plans as "not applicable" or thin, against a large budget, is flagged and needs an explicit rationale. It is a flag, not a ban.

### 4.9 Proportionality: planning burden against the management envelope
For each candidate route the recommendation shows the **estimated planning burden**, its **source** (benchmark, prior or measured) and its **uncertainty**, next to the **management envelope** of the current funded stage: its budget × a benchmark management fee (12%, labelled a convention). The practitioner estimate (~300K for a full suite, proportionate to ~2.5M at 12%) is a **labelled prior** with a wide interval, replaced progressively by effort measured on processed projects. Measured effort is metadata on the gate and approval episodes (no new record type). Where there is no monetary budget, effort-equivalent units are used and the 12% benchmark is not applied.

### 4.10 Cycle behaviour: progressive elaboration, Stage 17, Stage 18
- **Progressive elaboration is the expected pattern.** A first cycle carried by the PMP alone is normal; as the foundation becomes clearer, depth grows where it is needed, and the plans that grow go through foundation breakouts. A minimal cycle is legitimate because every route is recorded and growth is triggered by evidence.
- **Changing depth later (Stage 17)** goes back to the **plan foundation**: a breakout for a new or graduating plan, then the plan, then an approved PMP diff. A route is part of the baseline, so changing it is an approved baseline change. `Adaptation-Plan.md` remains the Stage 17 artifact that proposes the change; a route change takes effect only when approved. Whether `approve-adaptation-plan` provides that approval is open (§9).
- **Lowering depth** (a full plan returning to a section, or to not applicable) requires a recorded rationale and evidence that the need has reduced, and a showing that the floor and cap still hold. The full plan's approved baseline is archived (ADR-008 §4.6 history), and a baseline-substantiating plan can lower only to a section.
- **Reviewing the profile and standard (Stage 18):** each cycle, Stage 18 reviews them and feeds back to Intent and the Charter. Changes are damped like other strategic changes (ADR-009 §4.10–4.11) and approved as the Charter requires.

### 4.11 Ownership and routing
Each management plan has a declared owner role drawn from the stakeholder register: a department where one exists (for example procurement to Procurement; human resources to HR), and otherwise the Project Manager. Role names are free text because organizations differ, and a plan may carry several owner-tagged sections (the resource plan covers people and materials). Where only a PMP exists, everything routes to the Project Manager, and a non-PM role appears only once assigned. The Project Manager escalates plans to owners where they exist and remains accountable, and resolves seams that cross departments. The tooling may show an **advisory routing view**. The deciding role is recorded with every decision.

### 4.12 Learners advise; they never decide
There is one learner per knowledge area (nine learner policies), advisory only, and `low` authority if it becomes a policy. A learner learns from the recorded pairs of recommendation and decision (candidates: the route, whether a paragraph was sufficient, graduation, and accepted deviations) and may estimate planning burden from measured effort. It cannot approve or choose a route. This ADR does not claim `full`-authority decisions are trained on (ADR-001 §4.2). The design, including thin data per area, the shared-prior hypothesis, estimator and selection bias, belongs to the learner ADR.

### 4.13 Scope boundary and deferred decisions
This ADR does **not** define the plan templates, floors, caps or the definition of the standard, foundation breakouts, or first-round versus diff routing (the plan standards and tooling ADR); the per-plan approval gates and seam checks (the decision gates ADR); or the learner mechanics and autonomy governance (later ADRs).

**Deferred to a later decision:** the specific roles and bodies (sponsor, PMO, project manager, committees and other stakeholders), who declares the standard, and which approver applies to which trigger. This ADR refers to "the approver the Charter names".

## 5. Alternatives Considered

| Alternative | Reason for rejection |
|---|---|
| **Always generate the full suite (status quo)** | Imposes a burden independent of the project and out of proportion for small ones, which the Ideation Document already recognised for this project. |
| **Let the agent infer complexity or choose the route** | Contradicts ADR-003 §4.1 and §5: a self-grading agent has an incentive to understate effort. |
| **System-enforced hard blocks on floors and caps** | Contradicts the principle that these are human-decide gates and that the project team's use of the cycles determines what happens. Flags with recorded decisions keep the human accountable. |
| **Fixed size thresholds that map budget directly to a route** | A threshold can inform the recommendation but cannot capture opportunity, capability or ambition. |
| **A new `decide-tailoring-route` TaskPolicy** | The decision already lives in the Charter or PMP and passes existing human gates; a further gate adds ceremony (*provisional*, §9). |
| **Tailor each plan ad hoc with no recorded decision** | Produces hollow plans that pass as real, the failure found in the current baseline. |
| **Declare the profile and standard only in the PMP** | They state what the project wants to achieve and are revised at Stage 18 back to Intent, so they belong upstream; the PMP records the route derived from them. |
| **Hard-code the 300K and 12% figures** | A recollection and a convention, not measurements. They are a labelled prior and benchmark. |

## 6. Consequences

### Positive
- Planning effort is proportionate to the project, and the decision is explicit, recorded and attributable to a role.
- A small first cycle is legitimate, with a defined way to grow it and to say when a paragraph is not enough.
- A finding names a paragraph and so a plan, instead of failing the PMP as a whole.
- The cost of automation can be measured against a stated management envelope, giving a concrete benefit measure for the tooling.
- It reuses existing mechanisms: the ADR-003 declared profile, the ADR-008 §4.8 profile selection, existing gates, Stage 17 adaptation and ADR-009 damping.

### Negative
- A Charter section, an integration section and validation add ceremony; that cost is itself part of what the estimate must account for.
- Burden estimates start as a prior and stay uncertain for a long time: each project yields few observations, and only the route taken is observed.
- The three-part model is conceptual; until its terms have indicators the recommendation is qualitative.
- Flags rely on the team acting on them. A team that ignores flags still leaves a recorded decision, but the quality of the outcome depends on the team.
- The edition mismatch (§3, §9) means plan names and counts may later change.

## 7. Architectural Invariants

1. The route, and every accepted deviation from a floor, cap or expectation, is decided by a human; the system recommends only (§4.2, §4.6).
2. For every such decision both the recommendation and the decision, with the rationale and the deciding role, are recorded (§4.2).
3. The project profile, standard and approval limits are declared by humans in the Charter and are never inferred or reclassified by an agent (§4.5; ADR-003 §4.1).
4. Every plan has a recorded route; omission is never silent (§4.1).
5. Floors, caps and the baseline-substantiating expectation (cost, scope, schedule) are surfaced as flags; an over-cap section is always flagged and its resolution recorded (§4.2, §4.3).
6. The integration section has one home at a time, the Charter if it defines it and otherwise the PMP; the Charter prevails on conflict (§4.6).
7. A PMP or Charter change that introduces new floor amounts needs the approvers the Charter names in addition to the Project Manager, who signals the change (§4.7).
8. Where the Charter permits research funding, the PMP states only that funding until the cost foundation is done (§4.5).
9. Burden figures are labelled benchmark, prior or measured, and a prior is never shown as a measurement (§4.9).
10. Depth changes after the first cycle go back to the plan foundation through Stage 17 and are approved baseline changes; standard changes go through Stage 18 and are damped (§4.10).
11. Route decisions, effort metadata and approvals are `Episode` records; no new `LearningStore` record type (ADR-002 Invariant #2).
12. Learners are advisory, one per knowledge area, and never approve (§4.12; ADR-001 §4.2).

## 8. References
- [`scripts/orchestrate_pmbok.py`](../../scripts/orchestrate_pmbok.py) — `PLAN_MAPPING`, `target_processes`, `--mode full` / `--mode adapt`
- [`docs/policy-shapes/shared-complexity-profile.json`](../policy-shapes/shared-complexity-profile.json) — the declared complexity profile
- [`docs/project-docs/Project-Charter.md`](../project-docs/Project-Charter.md) — current Charter sections, including the M0.5 research stage
- [`docs/intent-to-outcome-chain-coverage.md`](../intent-to-outcome-chain-coverage.md) — Stage 17 tailoring, Stage 18 feedback
- PMBOK Guide 8th edition (licensed copy; paraphrased, not reproduced): sections 2.1.6.1, 2.1.6.2, 2.1.7, 3.1–3.4, 3.6 and Table 3-1
- Related: [ADR-001](./ADR-001-decision-authority-model.md) §4.2 — `full` authority is not trained
- Related: [ADR-002](./ADR-002-storage-backend-strategy.md) §7 Invariant #2 — five record types
- Related: [ADR-003](./ADR-003-evidence-gated-autonomy-thresholds.md) §4.1, §5 — declared, not inferred, complexity
- Related: [ADR-008](./ADR-008-pmbok-lifecycle-orchestration-and-pmp-adaptation-loop.md) §4.4, §4.6, §4.8, Invariant #4 — adaptation flow, baseline history, profile-based weighting, permanent human sign-off
- Related: [ADR-009](./ADR-009-intent-refinement-and-cognitive-feedback-loop.md) §4.10–4.11 — damping and rate-limiting
- Related: Ideation Document §4.2–4.9 — the earlier decision to name the scope mismatch

## 9. Open implementation questions — not resolved here
- **Depths:** three (full plan, PMP section, not applicable) is a provisional default; a fourth "short plan" level is not adopted.
- **Baseline-substantiating set:** cost, scope and schedule, provisional; whether "not applicable" for them is only a strongly flagged deviation (as written) or should be a hard rule.
- **Graduation caps:** how a section's cap is expressed (chapters, subsections, size) and its values per plan are plan-standards questions; the learner ADR may estimate where sections typically graduate.
- **Definition of "the standard":** its attributes, how it is expressed in checkable terms per plan, and what evidence supports changing it (plan standards ADR).
- **Per-plan overrides** of the project-level standard: not decided.
- **Integration section home:** whether the "Charter if defined, else PMP" rule applies to the whole section or per element (type, route per plan, owners). My lean: per element.
- **Approval route for later route changes:** whether `approve-adaptation-plan` (Stage 17) provides it or a Charter amendment or PMP change does.
- **Roles deferred (§4.13):** sponsor, PMO, project manager, committees and other stakeholders; who declares the standard; the approver per trigger; response times.
- **Charter scope:** the current Charter is scoped to Phase 1. Whether the profile and standard apply per phase or per project is open.
- **Edition and naming:** the repository uses 6th-edition numbering and plan names under "PMBOK 8" labels, while the 8th edition has seven performance domains and names the cost plan "financial management" and procurement "sourcing strategy". Whether the nine plans and nine learners are re-based is a plan standards decision.
- **Measuring planning effort:** which quantities are captured automatically (generation cost, revision count) and which are declared (breakout and review time) is an FDD question. The estimator and selection bias belong to the learner ADR.
- **Indicators** for each term of the three-part model, and the unit for projects without a budget.
- **Value thresholds** for the Project Manager's limits and the format of the escalation table (FDD).
- **The management fee benchmark:** the 12% figure is a convention; its source is not recorded here.
- **Registering hypotheses** (the full-suite burden estimate, the route recommendation's predictive value) in the Ideation Document before acceptance.

## 10. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Drafted, Proposed | Menno stated that project type, size and resources decide how much management-plan work a project needs, and recorded the burden estimate (~300K, ~12% fee, ~2.5M project) from experience. Recorded as a new decision, separate from ADR-008, which stays as accepted. |
| 2026-10-25 | Consolidated: per-plan routes and floors as flags with recorded recommendation and decision; cost, scope and schedule as baseline-substantiating plans with graduation; remedial foundation breakouts; Charter minimum baseline, approval limits and staged funding; integration section home (Charter, else PMP); sponsor approval for new floor amounts; ownership and routing; learners per knowledge area; PMBOK 8 grounding; roles deferred | Menno's clarifications across the review, and two external reviews assessed critically (a third is still to be assessed). Adopted or adapted: the BRU-008-04 context (no consistency check exists, so it is an intent), the ordering within planning, the `Adaptation-Plan.md` role, the demotion rules, and the standard's definition as an open item. Rejected: the reviews' scores and approval verdicts (not `approve-adr` results), a ban on "not applicable" for risk (a flag instead), the "Stage 6a/6b/6c" labels, and deprecating `Adaptation-Plan.md`. An over-cap invariant was reworded to "always flagged and resolved by a recorded decision", because the human decides. A stale cross-reference was fixed. |

---

## Provisional additions (2026-10-25, after the split)

- **Base minimum of Potential and Ambition.** Before a funded stage is authorized, the Charter shows at least a minimum of both, enough to see through that stage's uncertainty. It is stated qualitatively, with a rationale, until indicators exist. Potential minimum: the capacity to carry the stage (named capabilities, a visible evidence trail of shipped work, working habits). Ambition minimum: a stated vision and drive, plus how uncertainty will be handled (risk and issue escalation, mitigation plans, playbooks) so that courage can exceed fear. Below the minimum is flagged, not blocked; the human decides; the weakest-term cap applies. Research-first funding is the proportionate response to high uncertainty. Promote to an ADR only once confirmed in use.
- **Management-share benchmark not agreed.** The 12% figure is a recollection and Menno would judge it differently; the derived 2.5M project size is therefore not agreed either. Leave the benchmark blank until measured on processed projects, or until one is chosen.
- **Opportunity evidence.** Microsoft Scout adoption of the upstream SDK is real but its production volume is unchecked; the Vercel item (HYP-AL-017) is an issue Menno filed, with no recorded response; revenue and willingness to pay (HYP-AL-011) are unvalidated. Any further involvement should be recorded with its source before the Charter's opportunity statement cites it.
