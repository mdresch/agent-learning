# Epic 38: Packaged Contextual Learning

**Source ADR:** [ADR-038](../adr/ADR-038-packaged-contextual-learning.md) — Accepted (2026-10-30, Menno); Episode `f745c77b-0a2c-4e97-82d4-6f6936b2acd9`  
**Source BRD/FDD:** [BRD-038](../project-docs/Business-Requirements/BRD-038-packaged-contextual-learning.md) / [FDD-038](../project-docs/Functional-Design/FDD-038-packaged-contextual-learning.md)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-038, BRD-038 and FDD-038 (Approved 2026-10-30); adjudicated via `approve-user-stories` (robust utility 0.748, episode `3da3bcdf-7c13-4473-8613-081bc6fdfd6c`).

Six stories. Each rule sits in one story (LL-012). Contract tests are `tests/test_contextual_learner.py` (38.1, 38.2, 38.3) and `tests/test_contextual_cli.py` (38.4, 38.5, 38.6). BRU-038-10 has no story: HYP-AL-004 stays Testing, and the methodology catalog is not edited.

**Menno confirmed FDD-038 D1–D6 and ADR questions Q1–Q3 on 2026-10-30, each option A.** Stories 38.1 to 38.3 follow D6. Story 38.4 is the init rule in ADR-038 §4.3. Story 38.5 follows D1 and D3. Story 38.6 follows D2, D4, and D5. The worked numbers below are the checks in FDD-038 §3. Stories 38.1 to 38.6 are Ready for implementation.

Fixture for 38.1 and 38.2 ("the zero policy"): actions `a` then `b`, `feature_dim` 2, both weight rows `[0.0, 0.0]`, baseline 0, `LearnerConfig` learning rate and baseline decay overridden per criterion. On this policy every vector has probabilities `[0.5, 0.5]` until `apply_update` runs.

---

## Story 38.1 — The Weight-Row Update

**Status:** Ready — D6 confirmed 2026-10-30  
**As** a maintainer, **I want** one exported learner to apply the example's update to a contextual policy, **so that** I no longer copy that loop by hand.

### Acceptance Criteria

- **$AC_0$ (One Episode):** On the zero policy, one episode with `feature_vector` `[1.0, 2.0]`, action `a`, aggregate reward `1.0`, learning rate `0.4`, and baseline decay `0.9` stores rows `a: [0.2, 0.4]` and `b: [-0.2, -0.4]` within 1e-9, sets the baseline to `0.1`, and increases the version by 1.
- **$AC_1$ (Batch Mean):** On the zero policy, one call with learning rate `1` and two episodes — `[1.0, 0.0]` action `a` reward `1.0`, then `[0.0, 1.0]` action `b` reward `-1.0` — stores `a: [0.25, 0.25]` and `b: [-0.25, -0.25]` within 1e-9, and leaves the baseline at 0. Both episodes are scored on the starting weights.
- **$AC_2$ (Clip Stays In The Policy):** On the zero policy, one episode `[1.0, 0.0]`, action `a`, reward `1.0`, learning rate `100` puts `a: [50.0, 0.0]` and `b: [-50.0, 0.0]` in `extra["weight_deltas"]`, and stores the clipped rows `a: [10.0, 0.0]` and `b: [-10.0, 0.0]`. `logit_deltas` is `{}`.
- **$AC_3$ (Receipt):** `consumed_inputs` lists only the used episodes, each with the aggregate reward id that was kept. `episodes_used` equals that length.
- **$AC_4$ (Pure):** `contextual_reinforce.py` imports nothing from `numpy` and nothing from `agent_learning.storage`. `ContextualReinforceLearner` imports from `agent_learning` and from `agent_learning.learners`.

---

## Story 38.2 — Skipped Episodes Are Counted

**Status:** Ready — D6 confirmed 2026-10-30  
**As** an auditor, **I want** a missing or unusable vector to leave the weights alone, **so that** a hole is never trained as a zero vector.

### Acceptance Criteria

- **$AC_0$ (One Counter):** Each of these episodes, offered alone with action `a` unless the case says otherwise, leaves the zero policy's weights, baseline, and version unchanged, returns `episodes_used` 0 and `extra["reason"]` `"no actionable episodes"`, and increments exactly the named counter to 1: missing `feature_vector` and `feature_vector: null` → `skipped_missing_vector`; a tuple or a dict → `skipped_not_list`; length 1 → `skipped_wrong_length`; `[1.0, NaN]`, `["1", "0"]`, and `[True, 0.0]` → `skipped_non_finite`; `action_logprob` null with vector `[1.0, 0.0]` → `full_authority_excluded`; `action_id` null or unknown → `skipped_no_action`; no aggregate reward → `skipped_no_reward`.
- **$AC_1$ (First Match):** An episode with `action_logprob` null and no `feature_vector` increments only `full_authority_excluded`.
- **$AC_2$ (Context Is Not The Vector):** An episode whose only copy of `[1.0, 2.0]` sits in `context_features` increments `skipped_missing_vector` and does not change a weight.
- **$AC_3$ (Supplied Zeros Are Used):** `feature_vector` `[0.0, 0.0]`, action `a`, reward `1.0`, decay `0.9` counts as used, moves the baseline to `0.1`, increases the version by 1, and leaves both rows at `[0.0, 0.0]`.
- **$AC_4$ (Bad Reward):** An aggregate reward of `1.1` or `NaN` raises `ValueError` before any weight change, including when another episode in the same call is usable.

---

## Story 38.3 — One Learner, One Policy Class

**Status:** Ready — D6 confirmed 2026-10-30  
**As** a maintainer, **I want** each learner to reject the other policy class, **so that** a contextual weight row is never updated by the scalar rule.

### Acceptance Criteria

- **$AC_0$ (Contextual Learner):** `ContextualReinforceLearner.update` on a `SoftmaxPolicy` raises `TypeError` with the message `ContextualReinforceLearner requires a ContextualSoftmaxPolicy`, and that policy's logits are unchanged.
- **$AC_1$ (Scalar Learner):** `ReinforceLearner.update` on a `ContextualSoftmaxPolicy` raises `TypeError`, and that policy's `context_weights` are unchanged. A `SoftmaxPolicy` update from `ReinforceLearner` still runs and does not read `feature_vector`.

---

## Story 38.4 — Init Can Create The Contextual Policy

**Status:** Ready — init rule in ADR-038 §4.3, confirmed with this draft on 2026-10-30  
**As** an operator, **I want** `task-policy-init --feature-dim` to store a low-authority contextual snapshot, **so that** I can create this policy without writing the weight rows myself.

### Acceptance Criteria

- **$AC_0$ (Shape):** `--feature-dim 3` with two actions stores `policy_kind` `contextual_softmax`, `feature_dim` 3, a `[0.0, 0.0, 0.0]` row for each action, logits `{id: 0.0}` for each action, and `decision_authority` `low`. The decision-context and complexity fields written today are still written.
- **$AC_1$ (Source):** With `--decision-authority` omitted, `decision_authority_source` is `default`. With `--decision-authority low`, the source is `configured`. Both store authority `low`.
- **$AC_2$ (Full Refused):** `--feature-dim 3` together with `--decision-authority full` exits 2, names `feature-dim` and `full` on stderr, and stores no policy.
- **$AC_3$ (Bad Dimension):** `--feature-dim 0` and `--feature-dim -1` each exit 2 and store no policy.
- **$AC_4$ (Omitted Flag):** An init without `--feature-dim` stores no `context_weights` and no `feature_dim`, including when authority is `full`.

---

## Story 38.5 — Decide Requires The Feature List

**Status:** Ready — D1 and D3 confirmed 2026-10-30  
**As** an operator, **I want** a contextual decide to take the vector on the command line and refuse a bad one, **so that** the choice I record is the choice `choose` made.

### Acceptance Criteria

- **$AC_0$ (Refusal):** On a contextual snapshot, a missing `--features`, a JSON object, a list of the wrong length, a `bool` element, or a non-finite element exits 2, names `--features` on stderr, and leaves the store unchanged. The same flag on a scalar snapshot exits 2 and leaves that store unchanged.
- **$AC_1$ (Payload):** `--features "[1.0, 0.0]"` on a zero contextual policy prints `feature_vector` `[1.0, 0.0]`, `selection_mode` `sampled` or `greedy`, and `action_probabilities` equal to `ContextualSoftmaxPolicy.probabilities` of that list. No episode is stored.
- **$AC_2$ (Greedy):** With weights that make action `b` the unique maximum for `[1.0, 0.0]`, `--greedy` selects `b` and sets `logprob` from that probability. Equal probabilities select the earlier action in the snapshot.
- **$AC_3$ (Not The Scalar Gate):** Logits that rank `a` first, and context weights that rank `b` first for `[1.0, 0.0]`, make `--greedy` select `b`. The payload has no autonomy block. `--seed` changes only the sampled draw.
- **$AC_4$ (Evidence Opt-In):** A valid `--features` on a contextual snapshot that has `capture_decision_evidence` set exits 2 with the command's existing evidence message and writes nothing.

---

## Story 38.6 — Scalar Commands Leave The Weight Rows Alone

**Status:** Ready — D2, D4, and D5 confirmed 2026-10-30  
**As** a maintainer, **I want** `train` and a full-authority change to refuse a contextual snapshot, **so that** the unused logits are not trained by mistake.

### Acceptance Criteria

- **$AC_0$ (Train):** `train` on a contextual snapshot skips that task with a reason that names `ContextualReinforceLearner`, leaves `context_weights` and `logits` unchanged, and does not construct a `SoftmaxPolicy` from that snapshot.
- **$AC_1$ (Authority):** `task-policy-authority-set --authority full` on a contextual snapshot exits 2, names `full` and `contextual` on stderr, and does not change the snapshot or its `migration_records`.
- **$AC_2$ (Payload):** The printed payload of a contextual snapshot has no `action_probabilities` key. The printed payload of a scalar snapshot still has `action_probabilities`.
- **$AC_3$ (Scalar Train):** `train` on a scalar softmax snapshot does not skip it for the contextual reason.
