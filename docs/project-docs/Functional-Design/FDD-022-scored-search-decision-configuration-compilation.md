# FDD-022: Scored-Search Decision Configuration Compilation

**Source ADR:** [ADR-022](../../adr/ADR-022-scored-search-decision-configuration-compilation.md) — Accepted (2026-10-28)  
**Source BRD:** [BRD-022](../Business-Requirements/BRD-022-scored-search-decision-configuration-compilation.md)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-022 and BRD-022; adjudicated via `approve-fdd` (robust utility 0.729, episode `c8b4a59f-98ee-4fae-acd4-cb3df5689952`). Section 4 lists where this design departs from ADR-022 §4.1 to §4.4. Menno confirmed the departures L1 to L8 on 2026-10-30 (L1 and L6 as the options stated in this FDD). ADR-022's body is not amended in this approval.  

---

## 1. Architecture & Component Placement

1. **Pure module** `src/agent_learning/weight_compiler.py` holding `LabeledFrame`, `CompiledWeights`, `NoImprovement`, `with_weights`, `evaluate`, `objective`, `split_holdout`, `coordinate_ascent`, `propose` and `apply_compiled_config`. It uses the standard library and `DecisionFrame`, `DecisionCriterion`, `DecisionResolver` and `DecisionStatus` from `agent_learning.decision`, and `PolicySnapshot` from `agent_learning.types`. It imports nothing from `agent_learning.storage` and does no file I/O. The only random number is the seeded shuffle of `split_holdout`.
2. **Two commands** in `cli.py`: `policy-compile-weights`, which reads a dataset file and the active policy and writes a proposal file, and `task-policy-weights-adopt`, which applies a proposal to the stored policy (L6). They do every read and write of files and the store.
3. **`task-policy-decide`** calls `apply_compiled_config` on the frame it loads when the active snapshot carries compiled weights (L1). `DecisionResolver` is not changed.
4. **One policy shape** as data files: `docs/policy-shapes/approve-compiled-weights.actions.json` (the three actions of the other `approve-*` gates) and a profile that declares `requires_human_approval: true`, so the router of FDD-021 pins it without a change to that list.
5. **State in the snapshot** (BRU-022-10): `PolicySnapshot.metadata["criteria_weights"]` (criterion id to weight) and `metadata["compiled_weights_provenance"]`. Nothing else is stored; the proposal is a file.
6. **Package export:** the public names are re-exported from `agent_learning/__init__.py`.

---

## 2. Data Contract

### 2.1 Constants
| Name | Value | Meaning |
|---|---|---|
| `STEP_DEFAULT` | 0.05 | the coordinate-ascent step, and the floor of any weight (L2) |
| `BETA_DEFAULT` | 0.1 | the weight of the margin term (ADR-022 §4.1) |
| `HOLDOUT_FRACTION_DEFAULT` | 0.3 | the smallest held-out share (ADR-022 §4.1); at most 0.5 |
| `MIN_PART` | 5 | the fewest items in the training part and in the held-out part (L8) |
| `RESTARTS_DEFAULT` | 5 | start points tried |
| `MAX_SWEEPS_DEFAULT` | 20 | sweeps per start point at most (L5) |

### 2.2 Dataclasses
```python
@dataclass(frozen=True)
class LabeledFrame:
    frame: DecisionFrame
    label: str                  # the action id the human settled on
    labeled_at: str             # ISO 8601, when the label was recorded

@dataclass(frozen=True)
class CompiledWeights:
    weights: Mapping[str, float]      # a MappingProxyType over a copy; criterion id -> weight, positive, sum 1.0 within 1e-9
    train_accuracy: float
    holdout_accuracy: float
    baseline_holdout_accuracy: float  # the frames as stored (the weights in force) on the same held-out part
    holdout_margin: float             # mean margin of the held-out items under the compiled weights
    seed: int
    evaluations: int                  # resolver calls made by the search
    sweeps: int
    restarts: int
    proposed_at: str

@dataclass(frozen=True)
class NoImprovement:
    reason: str
    baseline_holdout_accuracy: float
    best_holdout_accuracy: float
```
Construction of `CompiledWeights` copies `weights` into a `types.MappingProxyType`. Mutating the dict the caller passed does not change the stored weights, and writing into `weights` raises (BRU-022-08).

### 2.3 The proposal file
`policy-compile-weights` writes one JSON object: `task_id`, `agent_id`, `policy_id` and `policy_version` of the snapshot it compiled against, the `CompiledWeights` fields, the dataset size and the split sizes, the earliest and latest `labeled_at`, and the time the compile took in seconds. A `NoImprovement` result is written the same way with `"improved": false` and no weights.

### 2.4 The dataset file
A JSON list of objects `{"frame": <frame object>, "label": "<action id>", "labeled_at": "<ISO 8601>"}`. The frame objects have the shape `DecisionFrame.from_dict` reads; the action space comes from the active policy.

### 2.5 Provenance in the snapshot
`metadata["compiled_weights_provenance"]` holds the proposal's hash (SHA-256 of its canonical JSON), the seed, the accuracies, the split sizes, the label time range, the approval episode id and the adoption time.

---

## 3. Behavior

1. **`with_weights(frame, weights)`** returns a new frame whose criteria have the given weights, in the frame's criterion order. It raises `ValueError` unless the keys are exactly the frame's criterion ids and every weight is finite and positive. Constraints, options and evidence are not touched (BRU-022-04).
2. **`evaluate(item, weights, snapshot) -> (predicted, margin)`** calls `DecisionResolver.resolve(snapshot, with_weights(item.frame, weights))`. The snapshot is the policy snapshot the resolver requires: its action space must equal the frame's, and `evaluate` does not read `criteria_weights` from it (that is `apply_compiled_config`). `predicted` is the `selected_action` id when the status is `resolved`, the `proposed_action` id when the status is `needs_user_feedback` (a reasoned recommendation that awaits the human's acceptance, which is the status of every recorded `approve-*` frame), and `None` for any other status, such as a tie that needs a person or a request for evidence, which earns no credit (L7). `margin` is the robust utility of the leading feasible option minus that of the runner-up, clipped to [0, 1], and 0.0 when fewer than two options are feasible.
3. **`objective(weights, items, snapshot, *, beta=0.1)`** passes that same snapshot to `evaluate`. It is the sum over items of `1` when `predicted` equals the label, plus `beta * margin`.
4. **`split_holdout(items, *, fraction=0.3, seed)`** raises `ValueError` unless `0.3 <= fraction <= 0.5`, `seed` is an integer, and both parts would hold at least `MIN_PART` items. It orders the items by `(labeled_at, label)`, shuffles them with `random.Random(seed)`, and returns the training part and the held-out part (L8).
5. **`coordinate_ascent(train, snapshot, *, step=0.05, restarts=5, max_sweeps=20, beta=0.1) -> CompiledWeights-like result`.** All items must share one set of criterion ids. The start points are, in order: the mean of the frames' own normalised weights; the uniform weights; then, for each criterion in sorted id order, a point with 0.5 on it and the rest shared equally; the first `restarts` of them. From a start point, a sweep tries for each criterion `+step` and `-step`: the candidate raises that weight, floors it at `step`, renormalises to sum 1, and is rejected if any weight falls below `step` (L2). A candidate is accepted when it raises the objective by more than 1e-12. A start point stops when a sweep accepts nothing or after `max_sweeps` sweeps. The result with the highest training objective wins, ties going to the earlier start point. No random number is used.
6. **`propose(train, holdout, snapshot, *, proposed_at, ...) -> CompiledWeights | NoImprovement`.** It passes that same snapshot into the search and the scoring. It raises `ValueError` if any `labeled_at` is not strictly earlier than `proposed_at` (BRU-022-06, L7). It runs `coordinate_ascent` on the training part, scores the compiled weights and the frames as stored on the held-out part, and returns `CompiledWeights` only if the held-out accuracy of the compiled weights is strictly greater than the baseline (BRU-022-07, L4); otherwise `NoImprovement`.
7. **`apply_compiled_config(frame, snapshot) -> DecisionFrame`** returns the frame unchanged when `snapshot.metadata` has no `criteria_weights`; otherwise `with_weights(frame, weights)`, raising `ValueError` if the criterion ids differ (L1). It runs no search.
8. **`policy-compile-weights --agent-id A --task-id T --validation-dataset FILE --seed N [--proposed-at ISO] --output-proposal FILE`.** It reads the active policy, loads and checks the dataset (L8), splits it, calls `propose` and writes the proposal file. A dataset item whose label is not an action id of that policy, or that lacks `frame`, `label` or `labeled_at`, makes the command exit non-zero and name the item. That check is in the command. `weight_compiler.py` does not open the dataset file. The command writes nothing to the store. `--proposed-at` defaults to the current time.
9. **`task-policy-weights-adopt --agent-id A --task-id T --proposal FILE --approval-episode ID`.** It checks that the proposal improved, that it names the active policy's id and version, and that the approval episode exists, belongs to `approve-compiled-weights`, and has `feedback_status` `adjudicated` with `decision_disposition` `accepted`. Then it stores a new version of the policy with `criteria_weights` and the provenance of section 2.5 (L6). Otherwise it exits non-zero and writes nothing.

**Worked checks (arithmetic, to be re-run when built).** A frame with criteria `c1`, `c2`, options `A` (supports 0.9 and 0.3) and `B` (0.4 and 0.8), one source per criterion at confidence 1.0 and `uncertainty_penalty` 0, run through the real resolver on 2026-10-29: weights `(0.7, 0.3)` give `A` 0.72 and `B` 0.52, status `resolved`, margin 0.20; weights `(0.5, 0.5)` give 0.60 and 0.60, status `needs_user_tie_break`, so no credit and margin 0; weights `(0.3, 0.7)` give `A` 0.48 and `B` 0.68, `B` selected, margin 0.20. With the label `A`, the objective term is `1 + 0.1 * 0.20 = 1.02` at `(0.7, 0.3)`, `0` at `(0.5, 0.5)` and `0.1 * 0.20 = 0.02` at `(0.3, 0.7)`.

**Measured on 2026-10-29 on a real frame (adr-037-approval, 4 criteria).** One `resolve` took about 0.14 ms. A full default search (4 criteria, 20 sweeps, 5 restarts, so 8 candidates per sweep) makes up to 800 evaluations per item, which is about 11 seconds for 100 items and about 56 seconds for 500 items. The stopping rule usually ends a start point well before 20 sweeps, so these are upper bounds (L5).

---

## 4. Departures from ADR-022 §4.1 to §4.4

Confirmed by Menno on 2026-10-30, L1 and L6 as the options in the "This FDD does" column. Each row is a place where ADR-022 does not fit the code that exists today, contradicts itself, or states a claim the measurement does not support. ADR-022's body is not amended in this approval.

| # | ADR-022 says | This FDD does | Why |
|---|---|---|---|
| L1 | "`DecisionResolver` reads the frozen compiled weights from `PolicySnapshot.metadata["criteria_weights"]`" | The resolver is unchanged; a pure `apply_compiled_config(frame, snapshot)` replaces a frame's weights, and `task-policy-decide` calls it when the snapshot carries compiled weights | The resolver reads weights from the frame it is given and never looks at the snapshot's metadata, so the sentence describes a behaviour that does not exist. Changing the resolver would alter every decision path and the ADR-005 comparison; a helper at the caller keeps the change small. Confirmed 2026-10-30 |
| L2 | Weights satisfy `sum = 1.0` and `w_i >= 0` | Weights are positive with a floor of one step (0.05) and sum to 1.0 within 1e-9 | The resolver rejects any criterion weight that is not positive, so a zero from the search would make the frame invalid. "Exactly 1.0" cannot hold in floating point |
| L3 | The configuration is `(w, lambda_uncertainty, epsilon_margin)` and the compiler optimises it | The search varies the weights only; the uncertainty penalty and the minimum margin stay at the frame's values and are recorded | ADR-022 §4.2 describes steps over weights only. The minimum margin changes whether a close result needs a person, not which option leads, so it does not enter the accuracy term. Searching `lambda` is a separate decision |
| L4 | Invariant 5: propose "if their holdout accuracy is at least that of the weights in force"; §4.4 test: `NoImprovement` "when holdout accuracy does not beat" them | Strictly greater | The two statements disagree on a tie. A tie is not an improvement, and changing a frozen configuration for no gain is the worse error |
| L5 | "Execution runs ... in < 10 seconds for validation sets of M <= 500 frames" | The time is measured and recorded with each proposal, and the search is bounded by `max_sweeps` and `restarts` | At 0.14 ms per resolve the default search costs about 56 seconds at 500 frames with 4 criteria, so the claim is not supported. The ADR itself asks for timings to be measured |
| L6 | The compile command writes `--output-snapshot`; "activating it needs an explicit human decision recorded as an episode"; no way to apply it is given | The compile command writes a proposal file only; `task-policy-weights-adopt` applies it to the stored policy as a new version when given an adjudicated accepted `approve-compiled-weights` episode; the shape declares `requires_human_approval` so the router pins it | The same pattern as FDD-021 K4: without it an approval is a record that changes nothing, or a hand edit. Confirmed 2026-10-30 |
| L7 | $\hat{y}_j$ is "the action chosen by the resolver"; $\text{Margin}_j$ is the leader's utility minus the runner-up's; labels must be "recorded before the compiled weights were proposed" | $\hat{y}$ is the selected action when the status is `resolved`, the proposed action when the status is `needs_user_feedback`, and none otherwise; the margin is on robust utility; `propose` refuses when any `labeled_at` is not before `proposed_at` | The resolver can return a tie that needs a person, and that is not a decision. A recorded `approve-*` frame is `needs_user_feedback` until the human accepts it, so that recommendation still earns credit. The ADR names the rule on label timing but gives no place where it is checked |
| L8 | `policy-compile-weights --task-id ... --validation-dataset tests/fixtures/governance/adr_validation_suite.json --output-snapshot ...`; "at least 30% is held out ... or k-fold with k >= 5 for small sets" | The command also takes `--agent-id` and `--seed`; the dataset format is stated (section 2.4); the split needs a fraction in [0.3, 0.5] and at least 5 items on each side; k-fold is not built | The example fixture file does not exist; the command needs the agent to find the policy; a split of a handful of items proves nothing, so it is refused |

---

## 5. Error Handling

| Scenario | Behavior |
|---|---|
| `with_weights` with keys that differ from the criterion ids, or a weight that is not finite and positive | `ValueError` naming it |
| Items whose frames have different criterion ids | `ValueError` naming the ids |
| `split_holdout` with a bad fraction, a non-integer seed, or a part smaller than `MIN_PART` | `ValueError` naming the cause |
| `propose` with a label time not strictly before `proposed_at` | `ValueError` naming the item |
| Held-out accuracy not strictly above the baseline | `NoImprovement`; nothing is changed |
| `apply_compiled_config` with different criterion ids | `ValueError` |
| A dataset item whose label is not an action id of the active policy, or that lacks `frame`, `label` or `labeled_at` | `policy-compile-weights` exits non-zero and names the item; the pure module does not read the file |
| `task-policy-weights-adopt` without a valid approval episode, with a proposal for another policy version, or with `improved` false | exits non-zero; nothing written |
| A snapshot with no `criteria_weights` | frames are used as stored |

---

## 6. Out of Scope

Searching `lambda` or the minimum margin; the Nelder-Mead surrogate; k-fold validation; changes to `DecisionResolver`, constraints or the ADR-003 gate; showing an improvement on real data; prompt compilation.

---

## 7. Decisions and Open Questions

1. **L1 to L8: confirmed (2026-10-30).** Menno confirmed them by asking for this FDD and Epic 22 to be approved. L1 keeps `DecisionResolver` unchanged and applies weights in `task-policy-decide`. L6 writes a proposal file and adopts it only through an adjudicated `approve-compiled-weights` episode. ADR-022's body is not amended in this approval.
2. **Open: the real labels cannot show an improvement.** Every recorded label is an accepted recommendation of the resolver, so baseline accuracy is 100% and `propose` can only return `NoImprovement`. Story 22.7 shows exactly that. Real disagreements are the missing data.
3. **Open: label independence in practice.** The same humans who wrote the weights adjudicated the frames, so agreement partly measures agreement with the author (ADR-022 §4.1). The `labeled_at` check ensures only ordering, not independence.
4. **Open: one weight vector for many frames.** Frames of one task may carry different weights as authored. The compiler replaces all of them by one vector per criterion id, so a task whose frames use different criteria cannot be compiled together.
5. **Open: overfitting.** The held-out part and `MIN_PART` limit it; a diverse set is the maintainer's responsibility (ADR-022 §6 Negative).
6. **Open: the routing interplay.** A compiled weight changes robust utilities and so the margins that ADR-021's router reads for full routes; recalibration of thresholds after adoption is not decided.
7. **Walkthrough sketch.** `examples/methodologies/22-scored-search/sketch.py` searches on all the data with no held-out part, allows a weight of zero, and has no strict-improvement rule; it is aligned with ADR-022 in the PR that confirms this FDD.

---

## 8. Test Data

*Real:* the 106 decision frames under `docs/policy-shapes/decision-frames/` and their results and adjudication episodes (48 frames and 97 results when ADR-022 was written). They make a real regression set: the weights in force must reproduce every human-accepted outcome. They carry no disagreement, so accuracy is 100% by construction and cannot show that compilation improves anything. *Gap:* decisions where a human disagreed with the resolver; and labels recorded before a proposal. The `tests/fixtures/governance/adr_validation_suite.json` named in the ADR does not exist. *Oracle:* the toy frame of section 3 and synthetic suites with a known weight vector, labelled as arithmetic checks, not as evidence.
