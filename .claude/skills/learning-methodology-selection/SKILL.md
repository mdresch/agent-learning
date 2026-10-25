---
name: learning-methodology-selection
description: Which learning methodology to apply to a new decision in agent-learning. Use before creating a TaskPolicy, choosing low vs full authority, or proposing a new methodology.
---

# Component: learning-methodology-selection (guidance, no code)

**Governing:** `docs/decision-making.md`, `docs/autonomy-complexity.md`, `docs/project-docs/Ideation-Document.md` §2.1 (landscape, 32 rows) and §2.2 (hypotheses).
**Status:** a lookup for agents and maintainers. It is hand-judged from the implemented SDK and the evidence in the Ideation Document. It is not a learned selector, and no selection episodes exist yet.

## Load-bearing constraints

- Authority, complexity tier and execution authorization are three separate axes (`decision-making.md`, "Keep the three autonomy axes separate"). Choosing a methodology never grants autonomy.
- Complexity is **declared by a human** in the policy's profile, never inferred from prose. `requires_human_approval` blocks learned autonomy whatever the evidence.
- Do not fabricate episodes or outcomes to make a methodology look viable. A methodology that needs data the repo lacks is "blocked", not "chosen".
- Only methodologies marked **Implemented** below can be applied today. Everything else is a drafted ADR or a candidate (Ideation §2.1.3). The ten ADRs 014-023 are Proposed, unapproved and unbuilt.

## What is available now (implemented)

| Methodology | Where | Use when |
|---|---|---|
| `full` authority, reasoned resolution (#3) | `DecisionResolver`, `task-policy-decide` then `task-policy-adjudicate` | Few recurrences, evidence is richer than a scalar, or the choice is high-impact. Output is a robust winner or a tie for a human. Never trains REINFORCE (`action_logprob is None`) |
| `low` authority, softmax bandit with REINFORCE (#2) | `SoftmaxPolicy`, `ReinforceLearner` | A small discrete action set, a recurring decision, and **contrastive** outcomes (both wins and losses recorded) |
| Reward shaping (#5) | reward shapers, local or LLM-judge | Turning raw metrics into the scalar reward that #2 consumes |
| Explicit human override (#6) | `metadata.feedback_status: accepted` / `rejected` | A human has decided. Grants autonomy for that task immediately and is revocable |
| Contextual softmax (#4) | `ContextualSoftmaxPolicy`, **example only, not packaged** | The best action depends on features. Packaging it is HYP-AL-004's open gap |
| Diff/baseline classification, category-level escalation (#20, #21) | `classify-diff-type`, `escalate-diff-response` | Already-built policies; reuse the shape, don't rebuild |
| Red-team validation (#19) | practice, not code | Test a policy's discriminative power before trusting it. Not yet a training signal |
| Active evidence-seeking (#12) | `InformationNeed` on the `NEEDS_EVIDENCE` path, **partial** | Resolver reports what evidence would change the winner; no automated seeking loop |

## Decision tree

1. **Is a human required to approve it, regardless of evidence?** (safety, compliance, financial, destructive). Set `requires_human_approval: true`. Use `full` authority. Stop.
2. **Is the decision rare, one-off, or evidenced by documents rather than repeated outcomes?** Use `full` authority (`DecisionFrame` with criteria, options and evidence). Expect ties to go to a human.
3. **Does it recur with a small discrete action set and an outcome you can score?** Use `low` authority.
   - **Outcomes contrastive (wins and losses)?** Softmax plus REINFORCE (#2).
   - **Outcomes positive-only (survivorship-biased history)?** REINFORCE plateaus here. HYP-AL-002 showed about 0.417 on the 146-episode `validate-intent-foundation` history. Today's only workaround is `full` authority. Thompson/UCB (#9, #10, HYP-AL-009) are the proposed fix and are **not built**.
   - **Does the best action depend on context features?** Contextual softmax (#4), example-only; packaging is required first.
4. **Is there a new `TaskPolicy` structurally similar to a converged one?** Warm-start (#15) would cut cold-start cost (about 200 episodes on `choose-repository-search`), but it is **not built** (ADR-020, HYP-AL-008).
5. **Is the thing being decided a ranking of N items by pairwise judgment?** Dueling-bandit ranking (#23, ADR-023) is a candidate, blocked: the raw pairwise judgments are not persisted anywhere (HYP-AL-015).
6. **Are the decision frame's criteria weights hand-set?** Scored-search compilation (#22, ADR-022, HYP-AL-010) is a candidate; it needs a labeled validation set.

## Tier and evidence check (after choosing)

Declare the complexity profile, then read the tier's gate from `autonomy-complexity.md`. For orientation only: `low` needs 3 scored outcomes, `standard` 20 with a 90% Wilson lower bound, `high` 50, `critical` 100. All criteria are conjunctive and the resolved values are returned in `autonomy.criteria`.

## When none of these fit

Check Ideation §2.1 for a candidate row (#8-#32) and its hypothesis in §2.2. If a candidate fits, say so, do not build it ad hoc: it goes through ADR, BRD, FDD and stories. If nothing fits, propose a new row with its premise and falsification criteria. Do not infer a methodology's viability from the existence of an ADR.

## Index of the Ideation landscape

Source of truth: [Ideation-Document.md](../../../docs/project-docs/Ideation-Document.md) §2.1 (table of 32 methodologies), §2.1.3 (ADR coverage) and §2.2 (hypotheses HYP-AL-001 to HYP-AL-024). This index is a copy for quick lookup; if it disagrees with the Ideation Document, the Ideation Document wins (LL-007: update both in the same change).

| # | Methodology | State | ADR | Hypothesis |
|---|---|---|---|---|
| 1 | Supervised fine-tuning | Excluded (frozen model); reopens if a hosted or fine-tuned model enters scope | none | none |
| 2 | RLVR / softmax bandit with REINFORCE | Implemented | none | HYP-AL-001 |
| 3 | Bayesian reasoned resolution | Implemented | none | HYP-AL-003 |
| 4 | Contextual bandit | Example only, not packaged | none | HYP-AL-004 |
| 5 | Pluggable reward shaping | Implemented | none | none |
| 6 | Durable human override | Implemented | none | none |
| 7 | Full ERL | Excluded (no resettable environment); reopens if one exists | none | none |
| 8 | Critique-to-evidence | Candidate | ADR-014 (Proposed) | HYP-AL-005 |
| 9 | Thompson sampling | Candidate | ADR-015 (Proposed) | HYP-AL-002, HYP-AL-009 |
| 10 | UCB | Candidate | ADR-016 (Proposed) | HYP-AL-009 |
| 11 | Epsilon-greedy | Candidate | ADR-017 (Proposed) | none |
| 12 | Active evidence-seeking | Partial | none | none |
| 13 | DPO-style pairwise preference | Candidate | ADR-018 (Proposed) | none |
| 14 | Meta-learning across policies | Candidate | ADR-019 (Proposed) | none |
| 15 | Warm-start / prior transfer | Candidate | ADR-020 (Proposed) | HYP-AL-008 |
| 16 | Model-based RL | Excluded as an acting policy; reopens as evaluation only (see #29) | none | none |
| 17 | Authority ensemble routing | Candidate | ADR-021 (Proposed) | none |
| 18 | Federated / multi-agent | Not applicable; reopens if HYP-AL-011 (hosted multi-tenant) is pursued | none | HYP-AL-011 |
| 19 | Red-team example generation | Practiced as validation, not as training signal | none | none |
| 20 | Diff/baseline classification | Implemented | none | none |
| 21 | Category-level escalation | Implemented, not yet trained | none | HYP-AL-007 |
| 22 | Scored-search compilation | Candidate | ADR-022 (Proposed) | HYP-AL-010 |
| 23 | Dueling-bandit ranking | Candidate, blocked on data | ADR-023 (Proposed) | HYP-AL-015 |
| 24 | LinUCB / LinTS | Candidate | none | HYP-AL-018 |
| 25 | Multi-stage credit assignment | Candidate, blocked (no `trace_id`) | none | none |
| 26 | Outcome-conditioned exemplar selection | Candidate | none | HYP-AL-024 |
| 27 | Prioritized experience replay | Declined for now | none | none |
| 28 | Conformal abstention | Candidate | none | HYP-AL-019 |
| 29 | Off-policy evaluation | Candidate, blocked (no logged action probability) | none | HYP-AL-020 |
| 30 | Change-point / non-stationarity handling | Candidate | none | HYP-AL-021 |
| 31 | Safe bandits with action masking | Candidate | none | HYP-AL-022 |
| 32 | Active-learning triage | Candidate | none | HYP-AL-023 |

## Known gaps (not fixed by this skill)

- Methodology choice is not recorded as an Episode yet. Record it in the ADR or decision note until a selection chain is designed.
- No `trace_id` on `Episode`, and no logged action probability for off-policy evaluation: those candidates (#25, #29) are blocked.

## Call sites

Read when creating a TaskPolicy (`docs/decision-making.md` CLI walkthrough), writing an ADR that picks a learning approach, or adding to the Ideation landscape.
