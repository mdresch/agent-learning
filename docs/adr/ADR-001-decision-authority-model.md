# ADR 001: Decision Authority Model — Learned vs. Reasoned TaskPolicy Resolution

## 1. Executive Brief
Every delegated decision in this SDK is owned by exactly one `TaskPolicy` per `(agent_id, task_id)`, with exactly one stable action taxonomy. That policy resolves through one of two mutually exclusive routes, selected by a persisted `decision_authority` field: `low` (a learned softmax bandit improved by REINFORCE over observed outcomes) or `full` (a reasoned Bayesian resolver evaluating a request-specific `DecisionFrame`). Both routes converge on the same `DecisionResult` and `Episode` lineage. This decision — and specifically the choice to keep both routes as *one* policy abstraction rather than two separate policy types — is already fully designed in `docs/decision-making.md` but has never been captured as a decision record with its real rejected alternatives named.

## 2. Status
**Accepted (2026-10-23)** — drafted 2026-10-23, approved by Menno the same day after review, including the §4.5 gap disclosure and the §9 Amendment Log corrections. Approved as a record of the intended design with that gap explicitly disclosed, not as a claim the gap is closed — closing it is tracked separately in BRD-001/FDD-001/Epic 1 Story 1.1.

## 3. Context
- `decision.py`'s `TaskPolicy.decide()` dispatches on `self.authority` (`DecisionAuthority.LOW` or `DecisionAuthority.FULL`), confirmed directly: `FULL` requires a `DecisionFrame` and calls `DecisionResolver.resolve()`; `LOW` forbids a frame and calls `SoftmaxPolicy.from_snapshot(...).choose()`. The two branches are enforced as mutually exclusive by `decide()` itself (`ValueError` if a frame is passed under `LOW`, or omitted under `FULL`).
- `docs/decision-making.md`'s own ERD (`agent-learning-erd.mermaid`) models this precisely: `TASK_POLICY ||--o| SOFTMAX_POLICY : delegates_low` and `TASK_POLICY ||--o| DECISION_RESOLVER : delegates_full` — two delegation edges from one policy entity, not two policy entities.
- Both routes return the same `DecisionResult` shape (`agent_id`, `task_id`, `policy_id`, `policy_version`, `selected_action`/`proposed_action` from the same `PolicySnapshot.actions`), and both feed the same `Episode` type once executed — confirmed in `decision.py`'s `DecisionResult`/`TaskPolicy.decide()`.
- A real, load-bearing asymmetry already exists and is documented: only `low`-authority episodes enter `ReinforceLearner` (`docs/decision-making.md`: "full-authority episodes remain scored audit evidence because their action was not sampled from the softmax behavior policy"). A `full`-authority decision always records `action_logprob: null` for exactly this reason — confirmed directly: `DecisionResolver.resolve()`'s `DecisionResult` construction for the resolved/reasoned path never sets `action_logprob` at all, so it falls through to the dataclass field's own default (`action_logprob: float | None = None`), whereas the learned (`low`-authority) path always computes and sets a real value from the sampled softmax probability.
- Migration between routes is a real, named, deliberately narrow operation — `task-policy-authority-set` (`docs/decision-making.md`: "Migrate an existing policy in place only after its owner grants the authority... Never create parallel low and full policies for one decision"). This is itself a design decision (reversible promotion, not permanent fork) with no record of why.
- Three distinct autonomy axes are explicitly kept separate by design (`docs/decision-making.md`'s "Keep the three autonomy axes separate" table): decision authority (`low`/`full`), complexity tier (`low`/`standard`/`high`/`critical`), and execution authorization (`supervised`/`autonomous`). Conflating any two of these was apparently a real risk worth naming explicitly in the docs — suggesting this was tried or considered and rejected, though the doc doesn't say so explicitly; this ADR records the three-axis separation as the decision, not the history of how it was arrived at.

## 4. Decision

### 4.1 One TaskPolicy, two routes, not two policy types
A delegated decision is modeled as one `TaskPolicy` entity with a configurable `decision_authority`, not as two separate policy classes a caller chooses between. This is deliberate: both routes need the same identity (`agent_id`/`task_id`), the same durable `PolicySnapshot`/`Action` lineage, and the same downstream `Episode`/`MetricResult`/`Reward` pipeline. Splitting them into separate types would have duplicated that entire lineage machinery for no behavioral benefit — `TaskPolicy.decide()`'s own dispatch-on-authority structure is evidence this was the chosen shape, not an accident of refactoring.

### 4.2 `full` authority is reasoned per-instance, never backed by learned softmax probabilities
A `full`-authority decision's action selection comes from `DecisionResolver.resolve()`'s Bayesian evidence aggregation (hard constraints → Pareto elimination → expected/robust utility → margin check), never from the policy's own learned logits. This is why `action_logprob` is always `null` on that path (§3) — the two routes are not two ways of arriving at the same kind of answer; `full` is reasoning from the *current* evidence, `low` is sampling from *accumulated history*. Mixing them (e.g., letting a `full` decision's outcome silently update the learned softmax logits) would corrupt the causal link between a sampled action's logged probability and its observed outcome, which `docs/decision-making.md`'s own REINFORCE math depends on.

### 4.3 Authority migration is in-place and mutually exclusive, not a fork
`task-policy-authority-set` changes an existing policy's active authority in place; it does not create a second policy or preserve two parallel ones for the same `(agent_id, task_id)`. At any point in time exactly one authority is active for a given decision. Migration is **reversible** — `low → full` and `full → low` are both real, supported transitions (§6 names the `low → full` direction explicitly) — but reversibility is not the invariant this section protects; mutual exclusivity is. **Corrected on review (2026-10-23):** an earlier draft of this heading read "one-directional per decision," which directly contradicted §3's "reversible promotion" framing and §6's "or back" — three different claims about the same operation. Nothing about this decision actually depends on migration being one-way; the real rule, confirmed against `task-policy-authority-set`'s own behavior, is mutual exclusivity, not direction.

### 4.4 The three autonomy axes stay independent
Decision authority, complexity tier, and execution authorization answer three different questions (§3's table) and must not collapse into one scalar "how much do we trust this." A `full`-authority resolution with a clean robust-utility win does not, by itself, grant execution autonomy — `requires_human_approval` and the complexity-tier gates (ADR-003) sit on top of authority, not inside it.

### 4.5 Known gap: the REINFORCE exclusion boundary is intended, not yet enforced in code
This ADR's §4.2 and §6 describe `full`-authority episodes as excluded from `ReinforceLearner` because they were never sampled from the behavior policy. **Checked directly against the current implementation, and that exclusion does not actually exist today:**
- `ReinforceLearner.update()`'s episode loop (`learners/reinforce.py:75-77`) only skips an episode when `action_id` is `None` or has no matching reward — it never inspects `action_logprob` or any authority signal.
- The only place `action_logprob is None` is consulted is `_importance_weight()` (`learners/reinforce.py:151-152`), which returns `1.0` for it — full, unweighted credit in the gradient step, not exclusion.
- `training/runner.py`'s `run_offline_batch()` queries episodes with `full_only=True`, but that flag means *complete* episodes (`Episode.is_full`, a data-completeness check unrelated to decision authority) — it is not an authority filter.
- `Episode` (`types.py`) has no `decision_authority` field at all, so nothing downstream can filter on authority directly even if it wanted to.
- `audit.py:562-563` confirms this is known, already-observed behavior: it emits a warning ("Missing behavior probability: importance weight uses the native fallback of 1") rather than excluding the episode.

The practical effect: a `full`-authority episode that gets a matching aggregate reward **does** enter the REINFORCE gradient update today, with full (`iw=1.0`) weight — which is exactly §5's second rejected alternative ("let a `full`-authority outcome also update the learned softmax logits"), not the decision this ADR actually records. This is a disclosed, tracked implementation gap, not a silent inconsistency: closing it is scoped in **BRD-001 / FDD-001 / the "Enforce the REINFORCE authority boundary" story**, to be picked up through `implement-story`. §6's Positive/Negative consequence bullets are annotated accordingly below.

## 5. Alternatives Considered

| Alternative | Reason for rejection |
|---|---|
| Two separate policy types (`LearnedPolicy`, `ReasonedPolicy`) instead of one `TaskPolicy` with an authority field | Would duplicate the entire durable lineage (snapshot/action/episode/metric/reward) for two policies serving the same conceptual decision, and would make authority migration a data-migration problem instead of a configuration change. |
| Let a `full`-authority outcome also update the learned softmax logits, so evidence is never "wasted" | Breaks the causal link REINFORCE depends on — a reasoned selection was never sampled from the behavior policy, so crediting it to that policy's logits would train on a propensity that was never actually used to choose. This is why full-authority episodes stay audit evidence, not training data. |
| A single, global autonomy threshold instead of three independent axes | Named explicitly as too permissive for consequential decisions and too expensive for routine ones (`docs/autonomy-complexity.md`'s own opening framing) — the complexity-proportional design (ADR-003) exists specifically because one threshold already failed this test. |

## 6. Consequences

### Positive
- One identity and one durable lineage per decision regardless of authority, so migrating a policy from `low` to `full` (or back) is a configuration change, not a data migration.
- The audit/training boundary (full-authority episodes never enter REINFORCE) is the *intended* design, and the resolver never populating `action_logprob` is the signal meant to carry it structurally rather than by caller convention — **but §4.5 found the signal is not actually consulted for exclusion today**, only for an importance-weight fallback. This bullet records the goal `ReinforceLearner` is accountable to, not yet its current behavior.
- Keeping the three autonomy axes independent means a well-evidenced `low`-authority policy cannot accidentally grant itself execution autonomy on a `requires_human_approval: true` decision — the axes compose rather than substitute for each other.

### Negative
- A `full`-authority decision's real evidence is **meant to be** excluded from this SDK's own primary learning mechanism (REINFORCE) — if an organization wants to eventually learn from reasoned decisions too, that requires a materially different mechanism, not an extension of the current one. ("Permanently" was the original wording here; removed because §4.5 found the exclusion itself isn't yet real, so permanence can't be claimed either way until it is.)
- Two routes sharing one policy abstraction means `TaskPolicy.decide()`'s own interface has authority-conditional requirements (a frame is required under `full`, forbidden under `low`) enforced at runtime via `ValueError`, not by two separate, narrower method signatures — a caller must know which authority is active before calling.

## 7. Architectural Invariants

Several of this ADR's decisions were already implicit; made explicit here as candidates for future automated validation:

1. Exactly one `TaskPolicy` exists per `(agent_id, task_id)`.
2. Exactly one `decision_authority` is active at a time for that policy.
3. The `low` and `full` resolution paths are mutually exclusive, enforced today at runtime by `TaskPolicy.decide()`'s `ValueError` checks (§3).
4. Only `low`-authority episodes should be valid REINFORCE training samples — **not yet enforced in code; see §4.5.** Today, any episode with a matching `action_id` and reward enters the gradient step regardless of authority.
5. Authority changes never create additional policy identities (§4.3).
6. Decision authority is independent of execution authorization and complexity tier (§4.4).

## 8. References
- [`decision.py`](../../src/agent_learning/decision.py) — `TaskPolicy.decide()`, `DecisionResolver.resolve()`, `DecisionResult`
- [`learners/reinforce.py`](../../src/agent_learning/learners/reinforce.py) — `ReinforceLearner.update()`, `_importance_weight()` — the gap cited in §4.5
- [`audit.py`](../../src/agent_learning/audit.py) — the existing "native fallback of 1" warning cited in §4.5
- [`docs/decision-making.md`](../decision-making.md) — full design writeup, math, CLI walkthrough
- [`docs/autonomy-complexity.md`](../autonomy-complexity.md) — three-axis autonomy separation and complexity tiers cited in §3 and §5
- [`docs/agent-learning-erd.mermaid`](../agent-learning-erd.mermaid) — entity relationship model cited in §3
- Related: [ADR-003](./ADR-003-evidence-gated-autonomy-thresholds.md) — evidence-gated autonomy, the layer above decision authority
- Related: BRD-001 / FDD-001 / "Enforce the REINFORCE authority boundary" story (§4.5) — scopes closing this gap

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-23 | Drafted, Proposed | Initial record of the already-implemented one-policy/two-route design |
| 2026-10-23 | §4.3 reworded (reversible + mutually exclusive, not "one-directional"); §4.5 added (REINFORCE exclusion gap, found by direct code reading, not assumed); §6 Positive/Negative bullets annotated to stop overstating current behavior; §7 Architectural Invariants added; reference links to `docs/autonomy-complexity.md` and ADR-003 fixed (were cited in prose but not linked in References) | Three independent external reviews of this ADR converged on the same §3/§4.3/§6 wording contradiction; verifying it against the file confirmed it was real. Tracing the §4.2/§6 REINFORCE-exclusion claim into the actual `reinforce.py`/`audit.py`/`training/runner.py` code (prompted by one review's "worth confirming how `ReinforceLearner` handles this" note, which none of the three reviews had itself verified) found the claim doesn't hold today — recorded honestly as a disclosed gap rather than silently rewriting the ADR to match the code, per Menno's instruction to keep the ADR describing the intended design and track the fix separately through BRD-001/FDD-001/implement-story |
