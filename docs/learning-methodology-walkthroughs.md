# Learning Methodology Walkthroughs

How to run, read and (where it exists) use each learning methodology that has a runnable example under `examples/methodologies/`. The catalog is `examples/methodologies/catalog.json`; the states come from Ideation §2.1.

This page teaches use. It does not show that any method works. Every example runs on invented data and prints `NOT EVIDENCE`. A benchmark that tests effectiveness is designed separately.

## Before you start

1. Run from the repository root with `uv run python …`, not bare `python`. A bare `python` here can import an older installed copy of `agent_learning` (examples 20 and 21 fail with `No module named 'agent_learning.governance'`, and example 03 fails near its end).
2. Every script prints its data label first. `SYNTHETIC` means invented for the demonstration.
3. Two kinds of entry:
   - **SDK** (methodologies 2, 3, 4, 5, 6, 12, 19, 20, 21): the example calls code that exists in `src/agent_learning`.
   - **Sketch** (methodologies 8, 9, 10, 11, 13, 14, 15, 17, 22, 23): plain Python of the ADR formulas. The method is not in the SDK, and its ADR is Proposed. The "In the real SDK" line says so and points to the ADR's code design.
4. Each folder's `README.md` states what the example does not show and what real data would be needed.

Output below was produced on 2026-10-28.

---

## Implemented or partly implemented (SDK)

### 2. REINFORCE bandit
**What it is.** A softmax policy over a few actions, nudged towards actions that earned more reward than a moving baseline.
**Use it when** the choice is among a small fixed set of actions, outcomes come back as scores, and there are both good and bad outcomes. It stalls when almost every outcome is good (HYP-AL-002).
**Run.** `uv run python examples/methodologies/02-reinforce-bandit/example.py`
**Read the output.** Five rounds of 40 episodes print `mean_reward`; then `probabilities before` (0.5 / 0.5) and `after` (`detailed` 0.715). The shift toward the action the invented rewards favored is the whole point.
**In the real SDK.** `agent-learn train --agent-id … --task-id …` runs `ReinforceLearner` over stored episodes; `agent-learn task-policy-decide` samples from the policy (`--greedy` for deterministic). Only `low`-authority episodes should train it (ADR-001; the exclusion is not yet enforced in code, ADR-001 §4.5).
**Does not show.** That it improves real outcomes or earns autonomy.

### 3. Bayesian reasoned resolution
**What it is.** A `full`-authority decision resolved from weighed, multi-source evidence, with no training.
**Use it when** the decision is rare or high-stakes, you can name criteria and evidence, and you need an auditable reason per instance.
**Run.** `uv run python examples/methodologies/03-reasoned-resolution/example.py`
**Read the output.** `status: resolved | selected: east` with robust utilities (east 0.871, west 0.466). The last line shows the same frame with human approval required: `needs_user_feedback`, with `east` as the proposal.
**In the real SDK.** Build a decision frame, then `agent-learn task-policy-decide --agent-id … --task-id … --decision-frame frame.json`, and record the human decision with `task-policy-adjudicate`. `docs/decision-making.md` has the frame format.
**Does not show.** That the evidence you supplied is right; the resolver only aggregates it.

### 4. Contextual bandit (example only)
**What it is.** A softmax policy whose preferences depend on a context vector.
**Use it when** the best action differs by a known context feature.
**Run.** `uv run python examples/methodologies/04-contextual-bandit/example.py`
**Read the output.** Both contexts start at 0.33 each; after training `enterprise` prefers `call` (0.99) and `consumer` prefers `email` (1.0).
**In the real SDK.** `ContextualSoftmaxPolicy` is exported; the trainable learner is written inside the example because it is not packaged.
**Does not show.** That a packaged learner is needed or that it earns autonomy.

### 5. Reward shaping
**What it is.** Metric scores combined into one bounded reward in [-1, 1], with penalties such as a slow response.
**Use it when** you have several metrics (completion, adherence, latency) and the learner needs one number.
**Run.** `uv run python examples/methodologies/05-reward-shaping/example.py`
**Read the output.** Three cases: good and fast `+0.640`; good but slow `+0.540` with a `latency` penalty of -0.1; poor and fast `-0.480`.
**In the real SDK.** `agent_learning.rewards.shape_episode_reward` with `ShapingConfig`; `agent-learn score` scores stored episodes.
**Does not show.** That these weights match what you value.

### 6. Durable human override
**What it is.** One human acceptance makes a choice eligible without the statistical gates; a rejection withholds it.
**Use it when** there is no outcome history yet and a person can vouch for the choice.
**Run.** `uv run python examples/methodologies/06-human-override/example.py`
**Read the output.** Three rows: no feedback `eligible=False`; one acceptance `eligible=True basis=user_acceptance audit_rate=0.0`; a rejection `eligible=False`.
**In the real SDK.** `agent_learning.autonomy.assess_autonomy` reads the human feedback from episode metadata (`feedback_status` of `accepted` or `rejected`, with the `correct_action_id`).
**Does not show.** That the human was right. See ADR-003 Invariant 6.

### 12. Active evidence-seeking (partial)
**What it is.** When the resolver lacks evidence, it reports which missing evidence would matter most, ranked by information gain.
**Use it when** a decision stalls on `needs_evidence` and you must choose what to gather first.
**Run.** `uv run python examples/methodologies/12-active-evidence-seeking/example.py`
**Read the output.** `status: needs_evidence`, then the needs by gain: constraint `residency` for `east` at 1.000 bits, criterion `capacity` for `west` at 0.800, `latency` at 0.200. Gather in that order.
**In the real SDK.** `TaskPolicy.decide` returns the information needs on its `DecisionResult`. Nothing fetches the evidence automatically.
**Does not show.** An automated gathering loop.

### 19. Red-team validation (practiced)
**What it is.** Running a persuasive but flawed proposal through the same policy as a sound one, to check the policy rejects it.
**Use it when** you want to test that a hard constraint really overrides a convincing argument.
**Run.** `uv run python examples/methodologies/19-red-team-validation/example.py`
**Read the output.** `real` resolves to `approve`; `flawed` resolves to `reject` with `ruled_out=['approve']`.
**In the real SDK.** The governance fixtures in `tests/fixtures/governance/adversarial-*.json` and the harness in `tests/test_governance.py` (AC7). These are single adversarial frames, not compliant/non-compliant pairs.
**Does not show.** Coverage of attacks you did not think of.

### 20. Diff classification
**What it is.** Classifying a proposed document change (correction, amendment, superseding) and deciding what happens to it.
**Use it when** documents change after approval and you must tell a typo fix from a reversed decision.
**Run.** `uv run python examples/methodologies/20-diff-classification/example.py`
**Read the output.** The typo fix is `correction_note`, lineage not frozen. The reversal with a "minor tweak" label is `new_superseding_adr`, `lineage_frozen=True`, escalated to a human.
**In the real SDK.** `agent_learning.governance.evaluate_governance_diff` with `DIFF_ACTIONS`.
**Does not show.** Accuracy on real diffs.

### 21. Category-level escalation
**What it is.** For one category of change, a low-authority policy learns whether to apply silently, apply with a notice, or escalate.
**Use it when** the same kind of change recurs and a human tires of confirming the harmless ones.
**Run.** `uv run python examples/methodologies/21-category-escalation/example.py`
**Read the output.** Before: all three actions at 0.333. After: `apply_automatically` 0.491, `apply_with_notification` 0.284, `escalate_to_human` 0.225. The last line is the boundary: lineage-changing diff types stay frozen from autonomy whatever is learned (ADR-007 Invariant 4).
**In the real SDK.** `ESCALATION_ACTIONS` in `agent_learning.governance` with `ReinforceLearner`.
**Does not show.** That the learned preference is safe on real changes.

---

## Candidates (sketches; not in the SDK)

Run each with `uv run python examples/methodologies/<folder>/sketch.py`. Outputs come from fixed seeds. "Design" gives the ADR section that specifies the module, signatures and tests.

### 8. Critique-to-evidence (ADR-014 §4.4)
**What it is.** Reviewer findings tagged `- [criterion: id] -0.20: reason` become bounded changes to criterion scores.
**Use it when** review comments should adjust a decision's evidence without rewriting the frame.
**Read the output.** `safety delta=-0.20 -> 0.50`, `clarity delta=+0.10 -> 0.60`, then a second `safety` finding `-0.30 -> 0.20`. Support moves by the tagged delta and is clipped to [0, 1].
**Real data needed.** The 30 triage records in `implementation-log.md`, tagged by a person.

### 9. Thompson sampling (ADR-015 §4.4)
**What it is.** A Beta posterior per action; sample one value per action and pick the highest.
**Use it when** outcomes are scores in [0, 1], and you want exploration that shrinks as evidence grows. The seed is recorded so a decision can be replayed.
**Read the output.** `pulls: {'a': 288, 'b': 12}`: the better action gets most pulls, the weaker one still gets a few.
**Real data needed.** A low-authority policy with real failures; the positive-only replay of the 41 approvals only exercises the failure mode of REINFORCE.

### 10. UCB (ADR-016 §4.4)
**What it is.** Choose the action with the highest `mean + exploration bonus`; ties break by pull count, then id. No random numbers.
**Use it when** you need every decision to replay exactly.
**Read the output.** `pulls: {'a': 226, 'b': 50, 'c': 24}`. More exploration than Thompson at the same horizon, and fully deterministic.
**Real data needed.** As methodology 9.

### 11. Epsilon-greedy (ADR-017 §4.3)
**What it is.** Mostly pick the best-known action; with a decaying probability explore, but only among actions declared reversible.
**Use it when** you need a plain baseline to compare the others against.
**Read the output.** `pulls: {'a': 285, 'b': 15}, explored: 26`. The count of explored steps is logged on purpose.
**Real data needed.** As methodology 9, plus a human declaring which actions are `reversible`.

### 13. Pairwise preference (ADR-018 §4.4)
**What it is.** Fit action logits from "A was chosen over B" pairs, anchored to a reference so they cannot drift far.
**Use it when** your signal is a human choosing between options, not a score.
**Read the output.** `logits: {'x': 3.58, 'y': -0.22, 'z': -3.36}`, ordered as the invented preferences imply, within the [-8, 8] clamp.
**Real data needed.** Override episodes. Today there are none: all 41 recorded episodes are accepted.

### 14. Hierarchical meta-prior (ADR-019 §4.4)
**What it is.** Pool the converged logits of several similar policies into a family prior, and start a new policy there.
**Use it when** you are starting several policies of one family.
**Read the output.** `mu: [1.2, -0.3, 0.13]` and small per-action variances. Large variances would mean the family is too different to pool.
**Real data needed.** At least four converged policies of one family with a shared action-role mapping.

### 15. Warm-start (ADR-020 §4.4)
**What it is.** Copy a donor's logits to a new policy through an explicit action map, damped by `tau` (default 0.70).
**Use it when** one similar converged policy exists.
**Read the output.** `full: accept 0.84 …` versus `damped: accept 0.73 …`. Damping flattens the start so exploration survives. The recipient still has to earn autonomy on its own outcomes.
**Real data needed.** One genuinely converged donor policy.

### 17. Authority routing (ADR-021 §4.5)
**What it is.** Decide per request whether to use the fast `low` policy or the reasoned `full` path, from entropy, margin and tier, with lifecycle gates pinned to `full`.
**Use it when** most requests are routine but a few are uncertain or critical.
**Read the output.** `routing checks passed (pinned, low, full, hysteresis, critical)`: the five rules hold on the sketch. There is no data output.
**Build first.** The REINFORCE exclusion in ADR-001 §4.5.

### 22. Scored-search compilation (ADR-022 §4.4)
**What it is.** Search criteria weights offline to agree better with labeled human decisions, then freeze them.
**Use it when** you have many labeled decisions where the human disagreed with the current weights.
**Read the output.** `accuracy 0.81 -> 1.00, weights [0.62, 0.28, 0.11]`. This sketch reports training accuracy; the real design requires a holdout (ADR-022 Invariant 5), so treat 1.00 as an illustration.
**Real data needed.** Disagreement cases. The 48 real frames are all accepted.

### 23. Dueling-bandit ranking (ADR-023 §4.5)
**What it is.** Rank items from head-to-head comparisons, asking next about the pair whose result is closest to 50:50.
**Use it when** you must rank a backlog and cannot compare every pair.
**Read the output.** `25 adaptive comparisons over 10 pairs: ranking [0, 1, 2, 3, 4]`: five items ranked in the right order from 25 comparisons, with every item compared at least twice first.
**Real data needed.** Real pairwise judgments of the real backlog; none are recorded.

---

## Not covered here
Methodologies without a runnable example (1, 7, 16, 18 and 24–32) have no walkthrough; their state and reasons are in `examples/methodologies/catalog.json`.
