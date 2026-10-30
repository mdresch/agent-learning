# BRD-038: Packaged Contextual Learning

**Source ADR:** [ADR-038](../../adr/ADR-038-packaged-contextual-learning.md) — Accepted (2026-10-30, Menno); Episode `f745c77b-0a2c-4e97-82d4-6f6936b2acd9`  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Accepted). The unapproved candidate is `PMP-BL-v1.0.0`.  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-038; adjudicated via `approve-brd` (robust utility 0.728, episode `c61347e0-7a70-41be-85a0-851ce9ee0b88`). Coordinate sentence corrected the same day to the confirmed answer. Not re-scored.  
**Stakeholders:** Menno (Sponsor/PM/maintainer); SDK adopters who need a different action per context; operators of `task-policy-init` and `task-policy-decide`

## Business Need

`ContextualSoftmaxPolicy` is already exported. It turns a caller-supplied numeric vector into action probabilities and keeps one weight row per action. The trainable learner is not exported. A caller who wants the policy to learn copies the loop in `examples/methodologies/04-contextual-bandit/`, and `task-policy-init` can create only the scalar softmax. Ideation §1.2 objective 4 names that gap. ADR-038 decides to export the learner and to add the init and decide flags. HYP-AL-004 stays Testing. Packaging the path does not confirm the hypothesis.

## Business Rules (BRU)

- **BRU-038-01 (One Class Each):** `ContextualReinforceLearner` accepts only a `ContextualSoftmaxPolicy`. `ReinforceLearner` accepts only a `SoftmaxPolicy` and continues to raise `TypeError` for the contextual policy (ADR-038 Invariant 1).
- **BRU-038-02 (The Example Update):** For one used episode the weight-row change is the update in ADR-038 §4.1. A batch averages those rows and multiplies by the learning rate once (FDD-038 §3). The learner calls `apply_update`. Clipping and the version bump stay inside `apply_update`.
- **BRU-038-03 (The Training Vector):** The learner reads `Episode.metadata["feature_vector"]` and does not read `context_features` (ADR-038 Invariant 2). The two fields stay different objects (ADR-004).
- **BRU-038-04 (Holes Are Skipped):** An episode with no `feature_vector`, a non-list, a non-finite element, or the wrong length is skipped and counted. The learner does not fill the hole with a zero vector (ADR-038 Invariant 3). A caller-supplied zero vector of the right length is a real vector and is used.
- **BRU-038-05 (Full Authority Stays Out):** An episode with `action_logprob is None` is skipped and counted (ADR-038 Invariant 4; ADR-001).
- **BRU-038-06 (Storage Boundary):** Weight rows stay in `PolicySnapshot.metadata["context_weights"]`. The learner writes no snapshot and no new `LearningStore` record type (ADR-038 Invariant 5; ADR-002).
- **BRU-038-07 (Low Authority Init):** `task-policy-init --feature-dim N` creates a low-authority snapshot with `policy_kind` `contextual_softmax`, `feature_dim` `N`, a zero weight row of length `N` on every action, and the unused scalar `logits` map still present. Omitting `--feature-dim` keeps today's scalar softmax. `--feature-dim` together with full authority stores nothing (ADR-038 Invariant 6).
- **BRU-038-08 (Decide Needs The Vector):** `task-policy-decide` on a contextual snapshot requires `--features`, a JSON list of length `feature_dim`. A missing list, a non-list, a non-finite element, or the wrong length exits 2 and writes nothing. The success payload carries the list that `choose` used, for the caller to copy onto the episode (FDD-038 D1).
- **BRU-038-09 (Autonomy Gate Unchanged):** ADR-003 is not edited. A contextual decide does not select from the scalar autonomy recommendation, because that recommendation is computed from the unused logits (FDD-038 D3).
- **BRU-038-10 (Hypothesis And Catalog):** These requirements do not mark HYP-AL-004 validated or refuted, and they do not edit the methodology catalog. The catalog stays `example_only` until the learner and the flags exist (ADR-038 §4.4).
- **BRU-038-11 (Scalar Train Must Not Move Weight Rows):** `train` on a contextual snapshot exits 2 and writes nothing. It must not build a `SoftmaxPolicy` from that snapshot and update the unused logits (FDD-038 D2).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| One-step exactness | On the worked one-episode case in FDD-038 §3, each stored weight matches the formula within 1e-9 after clipping |
| Batch mean | On the worked two-episode case, the applied rows are the mean of the one-episode rows, within 1e-9 |
| Holes | 0 weight changes when every episode lacks a usable vector; 0 invented zero vectors |
| Full authority | 0 episodes with `action_logprob is None` change a weight |
| Class wall | `ReinforceLearner` raises `TypeError` on a `ContextualSoftmaxPolicy`; `ContextualReinforceLearner` raises `TypeError` on a `SoftmaxPolicy` |
| Init | `--feature-dim` with full authority stores 0 policies; a low-authority init stores zero rows of length `N` and `policy_kind` `contextual_softmax` |
| Decide | 0 store writes when `--features` is missing or unusable; the success payload's `feature_vector` equals the list passed to `choose` |
| Scalar safety | 0 contextual snapshots are updated by `train` or by `ReinforceLearner` |
| Storage boundary | 0 new record types; the learner module imports nothing from `agent_learning.storage` and nothing from `numpy` |
| Hypothesis | HYP-AL-004 remains Testing; the catalog row for methodology #4 is not edited by this work |

## Out of Scope

- Marking HYP-AL-004 validated or refuted. Whether adopters needed the path stays the hypothesis.
- A schema for what each coordinate of the vector means. The package fixes the length only. The caller names what each coordinate means (confirmed 2026-10-30).
- LinUCB or LinTS (methodology #24, HYP-AL-018).
- Copying weight rows in an ADR-020 warm start.
- Editing ADR-003, the autonomy thresholds, or `assess_autonomy`.
- Teaching `train` or `LearningRunner` to call `ContextualReinforceLearner`. This BRD only refuses `train` on a contextual snapshot.
- An entropy bonus or an importance weight. The ADR formula has neither.
- Persisting an episode inside `task-policy-decide`. The command returns the vector; the caller records the episode (FDD-038 D1, confirmed 2026-10-30).
