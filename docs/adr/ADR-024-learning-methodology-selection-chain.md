# ADR 024: Learning Methodology Selection Chain

## 1. Status
**Proposed (2026-10-25)** — a deliberately small ADR, in the same shape as ADR-011. Not yet evaluated through `approve-adr`.

## 2. Context
- The Ideation Document (§2.1) surveys 32 learning methodologies. Nine are real or partly real, and most of the rest are candidates with their own drafted, unapproved ADRs (ADR-014 to ADR-023, none built).
- Choosing which methodology applies to a new decision is currently done by hand, from the documents. `.claude/skills/learning-methodology-selection/SKILL.md` writes that judgment down as a lookup, but it is guidance, not a mechanism, and nothing records which methodology was chosen or why.
- Complexity is declared by humans, not inferred by agents (ADR-003 §4.1). Decision authority, complexity tier and execution authorization are separate axes (`docs/decision-making.md`), so choosing a methodology must not grant autonomy.
- The pattern already proved in ADR-011 applies: the system recommends, a human decides, and both are recorded as an `Episode` with no new record type (ADR-002).
- Several candidates are blocked by missing prerequisites (no `trace_id` on `Episode`, no logged action probability, no persisted pairwise judgments). A selection that ignores this would recommend what cannot be built.

## 3. Decision
1. **A use-case profile.** Each decision that needs a methodology has a profile declared by a human: action space, feedback type, outcome polarity (contrastive or positive-only), context dependence, episode volume, drift, hard constraints, whether action probabilities are logged, and the existing complexity profile.
2. **Hard filters give a reason.** Mechanical rules remove methodologies that cannot apply, and each removal carries a stated reason (premise violated, or prerequisite missing). Nothing is dropped silently.
3. **Rank what remains by maturity.** Implemented, then example-only, then drafted, then candidate; implementation cost breaks ties. This ranking is a recommendation only.
4. **A human decides.** The human accepts the recommendation or chooses another eligible methodology, with a rationale. Choosing a blocked or unbuilt methodology is allowed only as a recorded request to build it, not as an applied policy.
5. **The rule table is hand-judged and versioned.** It starts from the Ideation Document and the evidence already in the repo. Learning the selector itself is deferred until recorded selections exist.

## 4. Invariants
1. The methodology is decided by a human; the system recommends only.
2. Every rejected methodology has a recorded reason; omission is never silent.
3. Recommendation, decision and rationale are recorded in `Episode.metadata` (no new record type, ADR-002).
4. The profile is declared by humans and never inferred by an agent.
5. Selecting a methodology never grants autonomy; the complexity tier and the evidence gate still apply unchanged.

## 5. Alternatives Considered
- **Skill and documents only (status quo):** cheap, but the choice and its reasons are not recorded, so nothing can later be checked or learned from.
- **A learned selector now (ADR-021 style):** no selection episodes exist, so training one would rest on fabricated or near-empty evidence.
- **Let an agent infer the profile:** contradicts ADR-003 §4.1; a self-grading agent has an incentive to understate difficulty.
- **One default methodology for everything:** HYP-AL-002 already shows that REINFORCE plateaus on positive-only history, so a single default fails on a known case.

## 6. Consequences
- A choice of methodology becomes inspectable: what was recommended, what was decided, and why the others were rejected.
- Most branches will end in "candidate, not built" until more methodologies exist. That shows which build would unlock the most use cases.
- The recorded selections are the evidence a later learned selector would need.
- The rule table can drift from the Ideation Document; it must be updated in the same change (LL-007).
- The module, the profile schema and the seed rule table need their own BRD, FDD and stories. This ADR decides only the shape.

## 7. Open questions
- Where the rule table lives (code, or a data file read by a pure module), and who may change it.
- The exact filter taxonomy and the feedback-type vocabulary.
- How this relates to ADR-021 (authority routing, which picks `low` or `full` per instance) and ADR-022 (scored search); this ADR selects a methodology per use case, those operate inside one.
- Whether already-built policies are profiled retroactively as seed cases.
- Whether the recorded selection should link to the later outcome of the policy it chose.

## 8. Amendment Log
- 2026-10-25: initial draft.
