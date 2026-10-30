# ADR 038: Packaged Contextual Learning

## 1. Executive Brief
`ContextualSoftmaxPolicy` is already in the SDK. It turns a caller-supplied feature vector into action probabilities and stores a weight row per action. The trainable learner is not in the SDK. The example at `examples/methodologies/04-contextual-bandit/` writes that update by hand, and `task-policy-init` cannot create this policy. Ideation §1.2 objective 4 names that gap. HYP-AL-004, which says the unpackaged example may not yet be worth exporting, stays Testing. This ADR decides to package the learner and the CLI path. It does not decide that the hypothesis is confirmed.

## 2. Status
**Accepted (2026-10-30, Menno)** — Design only. Episode: `f745c77b-0a2c-4e97-82d4-6f6936b2acd9`. Nothing in this ADR is built. The gaps in §7 stay open.

## 3. Context & Problem Statement
- **The policy is packaged. The learner is not.** `ContextualSoftmaxPolicy` is exported from `agent_learning.policy` and from `agent_learning`. `ReinforceLearner.update` accepts only a `SoftmaxPolicy`. A caller who wants the contextual policy to learn copies the loop in the example.
- **Objective 4 is unmet.** Ideation §1.2 asks for an exported, documented learner and a CLI path. The business case records that objective as not met. The methodology catalog still marks row #4 `example_only` with `adr: null`.
- **The feature vector is not the ADR-004 dict.** `Episode.context_features` is a caller-supplied dictionary for reward shaping and observability. ADR-004 says non-contextual action selection does not read it. `ContextualSoftmaxPolicy.choose` expects a numeric vector of length `feature_dim`. Those are different objects.
- **LinUCB is a later candidate.** Ideation §2.1 methodology #24 (HYP-AL-018) is the step beyond this policy. It is not built, and this ADR does not build it. ADR-021 routes between low and full authority. It does not train a contextual softmax.

## 4. Decision

### 4.1 Package the learner that the example already writes
Add `ContextualReinforceLearner` in `src/agent_learning/learners/contextual_reinforce.py` and export it beside `ReinforceLearner`. It accepts only a `ContextualSoftmaxPolicy`. `ReinforceLearner` continues to raise `TypeError` unless the policy is a `SoftmaxPolicy`.

For one episode with reward \(R\), baseline \(b\), feature vector \(\phi\), and probabilities \(\pi(\cdot \mid \phi)\), the weight-row update is the update the example applies by hand:

\[
\Delta W_a = \eta \, (R - b) \, \bigl(\mathbf{1}_{a = a_t} - \pi(a \mid \phi)\bigr) \, \phi
\]

The learner calls `policy.apply_update` with those rows. It does not write the snapshot itself. Clipping and the version bump stay inside `apply_update`, as they do today. No new package is added. The learner uses the standard library, as `ReinforceLearner` does.

### 4.2 Record the vector that `choose` used
The vector passed to `choose` is stored on that episode as `metadata["feature_vector"]`: a list of finite floats whose length is `feature_dim`. `context_features` is not that list. The learner does not read `context_features`.

An episode with no `feature_vector`, a non-list, a non-finite value, or the wrong length is skipped and counted. It is not trained as a zero vector. An episode with `action_logprob is None` is skipped, which is the ADR-001 rule that full-authority episodes stay out of a REINFORCE batch.

### 4.3 A CLI path that can create and call the policy
`task-policy-init` gains an optional `--feature-dim N`. When it is set, the new snapshot is low authority, `metadata["policy_kind"]` is `contextual_softmax`, `metadata["feature_dim"]` is `N`, and each action has a zero weight row of that length. The scalar `logits` map stays present and unused, as `from_actions` already does. Omitting `--feature-dim` keeps today's scalar softmax. `--feature-dim` with full authority is refused.

`task-policy-decide` on a contextual snapshot requires `--features`, a JSON list of length `feature_dim`. The episode recorded for that call copies the list into `metadata["feature_vector"]`. A missing list, or the wrong length, refuses the call and writes nothing.

### 4.4 What this decision does not do
- It does not change the ADR-003 autonomy gate.
- It does not mark HYP-AL-004 validated or refuted. Packaging is the objective 4 decision. Whether adopters needed the path remains the hypothesis.
- It does not extend ADR-020 warm-start to weight rows.
- It does not implement methodology #24.
- It does not add a LearningStore record type. Weight rows stay in `PolicySnapshot.metadata`, which is where they already live (ADR-002).
- The methodology catalog stays `example_only` until the learner and the CLI flags exist. This ADR does not edit the catalog.

### 4.5 Code design and test data
Design only. An FDD may confirm or change the signatures.

```python
class ContextualReinforceLearner(Learner):
    def update(self, policy: Policy, episodes: Iterable[Episode], rewards: Iterable[Reward]) -> LearnerResult: ...
    # TypeError unless policy is ContextualSoftmaxPolicy
    # skips: no feature_vector, wrong length, non-finite, action_logprob is None
```

Tests, not written yet: `tests/test_contextual_learner.py`. A hand-computed one-step update matches the formula. A missing vector does not change weights. `ReinforceLearner` still rejects a `ContextualSoftmaxPolicy`. A full-authority episode is skipped. `--feature-dim` is refused for full authority.

**Test data.** *Real:* none. The example uses invented contexts and rewards and says so. *Gap:* no stored episode carries `feature_vector`, because nothing records it yet.

## 5. Alternatives Considered
- **Leave the learner in the example.** Objective 4 stays unmet, and a caller who needs a per-instance decision keeps hand-building a full-authority frame, which is the failure HYP-AL-004 already recorded as one data point.
- **Teach `ReinforceLearner` to update both policy classes.** It calls `probabilities()` with no vector. One class would hide two updates. A wrong policy type should fail, as it does today.
- **Package LinUCB or LinTS instead.** Methodology #24 is a later candidate under HYP-AL-018. This ADR packages the policy the repository already has.
- **Train on `context_features`.** That dict is not a fixed-length numeric vector, and ADR-004 says action selection does not read it.

## 6. Consequences
- A caller can train `ContextualSoftmaxPolicy` through an exported learner, and can init and decide it from the CLI.
- Episodes recorded before this ADR have no `feature_vector`. They do not train the contextual policy. That is intentional.
- The caller still chooses what the vector means. A poor feature design learns a poor policy. This ADR does not supply a feature schema.
- HYP-AL-004 can still be refuted later. Shipping the path does not prove it was needed.
- ADR-020 does not copy weight rows. A new contextual policy still starts at zero until a later decision says otherwise.

## 7. Architectural Invariants
1. **One learner, one policy class.** `ReinforceLearner` accepts only `SoftmaxPolicy`. `ContextualReinforceLearner` accepts only `ContextualSoftmaxPolicy`.
2. **The training vector is `metadata["feature_vector"]`.** The learner does not read `context_features`.
3. **Wrong or missing vectors are not applied.** A zero vector is not invented to fill a hole.
4. **Full authority stays out of the batch.** `action_logprob is None` is skipped.
5. **No new record type.** Weight rows remain in `PolicySnapshot.metadata` (ADR-002).
6. **Low authority only.** `--feature-dim` on a full-authority init is refused.
7. **The autonomy gate is unchanged.** ADR-003 is not edited by this decision.

## 8. References
- Ideation-Document §1.2 objective 4 and §2.1 methodology #4
- HYP-AL-004, status Testing
- Business-Case record that objective 4 is not met
- `src/agent_learning/policy/contextual_softmax.py`
- `examples/methodologies/04-contextual-bandit/`
- ADR-001, ADR-002, ADR-003, ADR-004, ADR-020, ADR-021

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-30 | Proposed | Draft for the topic pillar "Packaged contextual learning". Not accepted. |
| 2026-10-30 | **Accepted by Menno** | Formally adjudicated and accepted through `approve-adr`; robust utility 0.744, expected utility 0.813; Episode `f745c77b-0a2c-4e97-82d4-6f6936b2acd9`. |

## Open questions
- Who names the coordinates of \(\phi\)? This ADR fixes the length, not the meaning.
- Should ADR-020 grow a weight-row donor map? Not decided here.
- HYP-AL-018 (LinUCB / LinTS) stays a separate candidate.
