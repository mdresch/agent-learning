# ADR 011: Project Tailoring and Route Decision

## 1. Status
**Accepted (2026-10-25)** — a deliberately small ADR. Evaluated through the `approve-adr` TaskPolicy (robust utility 0.661 vs. 0.060 for reject and 0.183 for revise; episode `6c76db96-36b1-4796-a1dd-6325c6ef5208`) and approved by Menno Drescher. The scores are an honest assessment that includes the ADR's known weaknesses. The wider design (Charter contents, approval limits, ownership, learners, burden figures, the PMBOK 8 mapping) is kept in [working notes](../design-notes/planning-redesign-notes.md) and is not decided here.

## 2. Context
- The PMBOK tooling always generates all nine management plans (`scripts/orchestrate_pmbok.py`, `--mode full`), whatever the project's size or resources. The Ideation Document already declined to fill the PMBOK sections for this project for that reason.
- Complexity is declared by humans, not inferred by agents (ADR-003 §4.1). `approve-pmp` is designed but not built, and its sign-off is permanently human (ADR-008 Invariant #4).
- The chain assigns tailoring to Stage 17, and Stage 18 feeds back to Intent. PMBOK 8 says planning should be sufficient but not more detailed than necessary, and that tailoring is decided at project initiation and revisited.

## 3. Decision
1. **A route per management plan.** Each plan is a full plan, a **PMP section**, or not applicable with a stated reason. A first cycle of "PMP only" is valid. The system recommends the route; a human decides it.
2. **Floors and caps are flags, not blocks.** Content below a plan's floor, over its cap, or a route that omits cost, scope or schedule (the plans that substantiate the PMP's baselines) is flagged with evidence. The project team decides. Both the recommendation and the decision, with the rationale, are recorded.
3. **The Charter sets the limits; the integration section holds the decision.** The Project Charter carries the minimum scope and baseline, the Project Manager's approval limits, the funding stage, the project profile and the project-level standard. The integration section (type, route per plan, owners) lives in the Charter if the Charter defines it, and otherwise in the PMP.
4. **Changes follow the cycles.** A change to a plan's depth goes back to the plan's foundation through Stage 17 and is an approved baseline change. A change to the standard goes back to Intent through Stage 18, damped against noise.
5. **Foundation breakouts are remedial for sections.** A PMP section that fails its standard or outgrows its cap triggers a breakout for that plan. A sufficient section needs none.

## 4. Invariants
1. The route and any accepted deviation are decided by a human; the system recommends only.
2. Every plan has a recorded route; omission is never silent.
3. Recommendation and decision are both recorded as `Episode` records (no new record type, ADR-002).
4. The profile, standard and approval limits are declared by humans and never inferred by an agent.
5. The integration section has one home at a time; the Charter prevails on conflict.

## 5. Alternatives Considered
- **Always generate all nine plans (status quo):** imposes a burden independent of the project, and a hollow plan can pass as a real one.
- **Let an agent infer complexity or choose the route:** contradicts ADR-003 §4.1, since a self-grading agent has an incentive to understate effort.
- **System-enforced blocks on floors and caps:** these are human-decide gates; flags with recorded decisions keep the human accountable and the team in control.
- **Tailor ad hoc with no recorded route:** leaves silent omissions, the failure found in the current baseline.

## 6. Consequences
- Planning effort can be proportionate to the project, and a minimal first cycle is legitimate.
- The decisions rely on the team acting on flags; the record shows what was recommended and what was decided.
- Plan standards (floors, caps, the standard's definition), decision gates, learners and role mapping need their own later decisions (learner decisions are made per plan in §4.4.1 of ADR-025 to ADR-033). Decision 3 bundles the Charter's contents with the integration section's home and will likely seed its own Charter ADR once those contents harden.

## 7. Open questions
See the [working notes](../design-notes/planning-redesign-notes.md). The main ones: the three route depths are provisional, whether omitting cost, scope or schedule should ever be a hard rule, whether the integration-section rule applies per element, and whether `approve-adaptation-plan` approves later route changes.

## 8. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Reduced from a long draft to this small ADR; the full draft moved to working notes | The long draft layered many unhardened decisions into one ADR, which is hard to maintain. Only decisions confirmed repeatedly stay here. Menno's review feedback and three external reviews were assessed critically; their fixes are listed in the working notes and applied as items harden. |
| 2026-10-25 | Added a short Alternatives Considered section; reworded Invariant 5 to "prevails on conflict" | A fourth review noted the light ADR had dropped alternatives. `approve-adr` has an `alternatives_considered` criterion and the earlier ADRs carry the section. The invariant no longer pre-commits to the per-element question left open in §7. |
| 2026-10-25 | Accepted | Evaluated through `approve-adr` (`task-policy-decide`, then Menno's acceptance via `task-policy-adjudicate`, then `task-episode-register`): robust utility 0.661 vs. 0.060 (reject) and 0.183 (revise), episode `6c76db96-36b1-4796-a1dd-6325c6ef5208`. Approved directly by Menno ("ADR 011 approved"). |
| 2026-10-28 | Pointer to per-plan learner decisions | §6 notes that learner decisions are made in §4.4.1 of ADR-025 to ADR-033. No decision in this ADR changed. Re-approved 2026-10-29 under `approve-adr` (adjudicated accept, robust utility 0.734 vs. 0.044 reject and 0.110 revise, episode `a17fb5ab-6033-4ec7-954d-578e39131b55`). |
