# BRD-024: Learning Methodology Selection Chain

**Source ADR:** [ADR-024](../../adr/ADR-024-learning-methodology-selection-chain.md) — Accepted (2026-10-26, Menno); Episode `f99f1078-db8f-4575-9bb4-77a95ef73b97`. Open questions resolved by Menno on 2026-10-28 (ADR-024 §7).  
**Governing Baseline:** `PMP-BL-v1.1.0` (Phase 2). Epic 24 is not in the baseline's authorized execution bands (Band C: Epics 14, 18; Band D: Epics 16, 21, 22, 38), so building it needs a scope decision first (FDD-024 §7 item 5). Drafting the requirements does not.  
**Status:** Approved (2026-11-09, Menno) — derived from Accepted ADR-024; adjudicated via `approve-brd` (robust utility 0.805, episode `994c2be9-ec82-4de7-9cc3-35f642f7a170`). Epic 24 remains outside the authorized PMP-BL-v1.1.0 scope; this approval does not authorize implementation.

**Stakeholders:** Menno (Sponsor/PM/maintainer, who declares profiles and decides); agents and maintainers who create a `TaskPolicy` and today read `.claude/skills/learning-methodology-selection/SKILL.md` by hand; auditors who must see why one methodology was chosen and why the others were not  

## Business Need

Picking the learning methodology for a new decision is done by hand today. The `learning-methodology-selection` skill writes the judgment down as a decision tree, and the methodology catalog (`examples/methodologies/catalog.json`, `agent_learning.methodology_catalog`, ADR-036) records the state of each of the 32 methodologies. Neither records which methodology was chosen for a decision, what was recommended, or why the others were set aside. ADR-024 decides the shape that closes this gap, in the same form as ADR-011: a human declares a profile of the decision, mechanical filters remove the methodologies that cannot apply and say why, the rest are ranked by maturity as a recommendation, and a human decides. The recommendation, the decision and the rationale are stored in `Episode.metadata`. Choosing a methodology grants no autonomy.

This BRD turns that decision into rules that can be built and tested. It reuses the catalog for each methodology's state and the existing `ComplexityProfile` for the complexity part of the profile. What is new is the profile schema, the versioned rule table, the filter with its reasons, the ranking, the decision record and its episode metadata. No selection has been recorded yet, and no rule has been checked against a real decision.

## Business Rules (BRU)

- **BRU-024-01 (Human-Declared Profile):** Each decision that needs a methodology has a use-case profile declared by a human. It covers the action space, the feedback type, the outcome polarity (contrastive or positive-only), the context dependence, the episode volume, the drift, the hard constraints, whether action probabilities are logged, and the complexity profile. A profile not marked as declared by a human, or with no declaring role, is rejected. Nothing in this chain infers a profile from prose, episodes or an agent's own output (ADR-024 §3.1, Invariant 4; ADR-003 §4.1).
- **BRU-024-02 (Closed Vocabulary):** Each profile field takes a value from a small closed list. Feedback type is one of scalar reward, binary outcome, ordinal preference, textual critique or none. An unknown field or an unknown value is rejected with the field and value named, as the plan lint does. A list grows only through a change to the rule table's version (ADR-024 §7, vocabulary; ADR-012).
- **BRU-024-03 (Complexity Profile Reused):** The complexity part of the profile is the existing ADR-003 complexity profile, validated by the existing rules. The selection records it and does not change it (ADR-024 §3.1, §2).
- **BRU-024-04 (Every Methodology Accounted For):** Every methodology in the catalog ends a selection either eligible or rejected, exactly once. A selection whose rule table and catalog do not name the same methodologies is refused. Omission is never silent (ADR-024 §3.2, Invariant 2).
- **BRU-024-05 (Every Rejection Has A Reason):** Each rejected methodology carries at least one reason from a closed list of reason codes, with a detail naming the profile field, the catalog state or the prerequisite that caused it. The ADR names two reasons, premise violated and prerequisite missing; the list adds a third, declined, for a methodology the catalog marks declined (ADR-024 §3.2, §7; Invariant 2; FDD-024 D3, confirmed 2026-11-09).
- **BRU-024-06 (Prerequisites Are Checked):** A methodology whose prerequisite is missing is rejected with the reason prerequisite missing and the name of the prerequisite. The ADR names three: a trace id on `Episode`, a logged action probability, and persisted pairwise judgments (ADR-024 §2, §3.2).
- **BRU-024-07 (Ranked By Maturity):** The eligible methodologies are ranked implemented, then example-only, then drafted, then candidate. Implementation cost breaks ties. The order is deterministic: the same profile, rule table and catalog give the same order (ADR-024 §3.3; FDD-024 D4, D6).
- **BRU-024-08 (Recommendation Only):** The first-ranked eligible methodology is the recommendation. The system never records a recommendation as a decision. When nothing is eligible, there is no recommendation (ADR-024 §3.3, Invariant 1).
- **BRU-024-09 (A Human Decides, With A Rationale):** A decision is valid only when marked as made by a human, with the deciding role and a rationale. The human may accept the recommendation or choose another eligible methodology. A methodology rejected for a premise violation, or as declined, cannot be chosen (ADR-024 §3.4, Invariant 1; FDD-024 D3).
- **BRU-024-10 (Unbuilt Means A Build Request):** Choosing a methodology that is not implemented is recorded as a request to build it, never as a policy to apply. A methodology rejected only for a missing prerequisite may also be chosen, as a build request only (ADR-024 §3.4; FDD-024 D7, confirmed 2026-11-09).
- **BRU-024-11 (Recorded In Episode Metadata):** The profile, the eligible list, every rejection with its reasons, the recommendation, the decision, the deciding role, whether a human decided, the rationale, whether the decision departed from the recommendation, the rule table version and the task id of the decision being profiled are stored as one plain record in `Episode.metadata`. Outcomes are read later from that task's own episodes. Nothing is written back, and no `LearningStore` record type is added (ADR-024 §3.3, Invariant 3, §7 outcome link; ADR-002 Invariant #2).
- **BRU-024-12 (No Autonomy Granted):** A selection never changes a policy's decision authority, complexity profile, tier, autonomy thresholds or feedback status. The selection is recorded on its own task, never on the profiled task (ADR-024 Invariant 5; `docs/decision-making.md`, "Keep the three autonomy axes separate"; ADR-003).
- **BRU-024-13 (A Versioned, Hand-Judged Rule Table):** The rules are a versioned JSON data file read by a pure standard-library module, like `catalog.json`. It is hand-judged from the Ideation Document and the evidence in the repository. A change to it goes through a pull request that Menno approves and raises its version (ADR-024 §3.5, §7 rule table).
- **BRU-024-14 (Checked Against The Ideation Document):** A test checks the rule table against Ideation §2.1 so that the two cannot drift silently: the same methodology ids, each row citing its Ideation row. A change to either is made in the same change as the other (ADR-024 §6, §7; LL-007).
- **BRU-024-15 (Retroactive Seed Cases):** The real, already-built policies are profiled as seed cases, each flagged `retroactive`, so the rules can be checked against the methodology each one actually uses. Their profiles are declared by Menno. No episode or outcome is invented (ADR-024 §7 seed cases, Invariant 4).
- **BRU-024-16 (Layers, Not Calls):** The selection may recommend authority routing (ADR-021) or scored-search compilation (ADR-022), which are catalog methodologies, but it never imports or calls them (ADR-024 §7, relation to ADR-021 and ADR-022).
- **BRU-024-17 (No Learned Selector, No Claim Of Effectiveness):** The selector is not learned and is not trained on recorded selections. No selection has been recorded and no rule has been checked against a real decision, so nothing is claimed about the quality of a recommendation (ADR-024 §3.5, §5).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Declared profiles | 100% of profiles without `declared_by_human` true and a non-blank role are rejected; 0 functions in the module build a profile from anything but a declared mapping |
| Vocabulary | 100% of unknown fields and values rejected, naming the field and value |
| Coverage | for every tested profile, eligible plus rejected equals the catalog, each id once; 100% of rule tables whose ids differ from the catalog's are refused |
| Reasons | 0 rejections without a reason code from the closed list and a non-blank detail |
| Determinism | the same inputs give the same eligible order and recommendation on every call; the worked fixtures of FDD-024 §3 give the stated orders |
| Recommendation | 0 selections that record a recommendation as a decision; a selection with nothing eligible has no recommendation |
| Decisions | 0 valid decisions without a human, a role and a rationale; 0 valid decisions on a methodology rejected for a premise or as declined; 0 unbuilt methodologies recorded as applied |
| Episode record | 100% of records round-trip through `json.dumps` and `json.loads` and carry every field of FDD-024 §2.5 |
| Autonomy | 0 changes to any snapshot, complexity profile, tier, threshold or feedback status by the module; the selection's task id is never the profiled task id |
| Rule table | 32 rows, ids equal to the Ideation §2.1 ids and to the catalog ids; every value in the closed lists |
| Storage boundary | 0 new record types; 0 imports from `agent_learning.storage`, `agent_learning_ext.routing` or `agent_learning_ext.weight_compiler` in the module; 0 edits to `src/agent_learning/` |
| Evidence | 0 claims that a recommendation is correct or useful; seed cases labelled `retroactive` |

## Out of Scope

- A learned selector, and any training on recorded selections (ADR-024 §3.5, §5).
- Inferring a profile from prose, episodes or an agent's output (ADR-024 Invariant 4).
- Changing a methodology's state in the catalog or the Ideation Document. The selection reads the state; under FDD-024 D5 the states are updated by a separate change that Menno approves, outside Epic 24.
- Building any methodology a selection requests. A build request goes through its own ADR, BRD, FDD and stories.
- Calling the router (ADR-021) or the weight compiler (ADR-022), and wiring a selection into `task-policy-init`.
- Editing ADR-003, the autonomy thresholds, `ComplexityProfile` or `assess_autonomy`.
- Writing the selection Episode to a store from a new command. Under FDD-024 D8 the module returns metadata only and the caller writes the Episode.
- Generating the rule table from the Ideation Document. The table is hand-judged (ADR-024 §3.5).
