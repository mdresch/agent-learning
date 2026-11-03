---
name: thompson
description: Guidance for Thompson sampling (Beta-Bernoulli posterior, seeded and replayable draws) in agent-learning (ADR-015, Epic 15).
---

# Skill: thompson (agent-learning)

## Overview
Thompson sampling picks an action by drawing one value per action from its Beta posterior and taking the highest draw. The posterior lives in `PolicySnapshot.metadata`; no new record type exists (ADR-002). This skill covers `src/agent_learning/policy/thompson.py` and `src/agent_learning/learners/thompson.py`.

## Governing Specifications & Contracts
- **Architecture:** [`docs/adr/ADR-015-bayesian-bandit-posterior-sampling.md`](../../docs/adr/ADR-015-bayesian-bandit-posterior-sampling.md)
- **Business Requirements:** [`docs/project-docs/Business-Requirements/BRD-015-bayesian-bandit-posterior-sampling.md`](../../docs/project-docs/Business-Requirements/BRD-015-bayesian-bandit-posterior-sampling.md)
- **Functional Design:** [`docs/project-docs/Functional-Design/FDD-015-bayesian-bandit-posterior-sampling.md`](../../docs/project-docs/Functional-Design/FDD-015-bayesian-bandit-posterior-sampling.md)
- **User Stories:** [`docs/user-stories/epic-15-bayesian-bandit-posterior-sampling.md`](../../docs/user-stories/epic-15-bayesian-bandit-posterior-sampling.md)
- **Test Contracts:**
  - `tests/test_thompson_seed.py` (Story 15.1: seed and replay)
  - `tests/test_thompson_policy.py` (Story 15.2: posterior state in the snapshot)
  - `tests/test_thompson_choose.py` (Story 15.3: choosing by probability matching)
  - `tests/test_thompson_learner.py` (Story 15.4: the conjugate update and the ceiling)
  - `tests/test_thompson_reinforce_guard.py` (Story 15.5: Thompson episodes are invisible to `ReinforceLearner`)

## Load-Bearing Constraints & Invariants
1. **Seed:** `seed_for(policy_id, request_id, timestamp)` is `int(HMAC-SHA256(key=policy_id, msg=request_id + "|" + timestamp).hexdigest()[:16], 16)`. The `"|"` separator is fixed so `("ab", "c")` and `("a", "bc")` differ. An empty argument raises `ValueError` naming it.
2. **Replay:** `replay(record, policy_id)` re-derives the seed, redraws from the recorded posterior in the order of its `alpha` keys, and returns the redraw. A seed mismatch raises `ValueError` ("seed"); a redraw that differs from `sampled_payoffs` raises `ValueError` ("version"): CPython does not promise the same Beta stream across versions, so that is a version difference, not tampering (FDD-015 §7 item 4). It never reads the store and never mutates the record.
3. **`replay` takes the policy id** because the FDD-015 §2.3 record does not hold it (interpretation I2, FDD-015 §7 item 6).
4. **Purity:** the module imports only standard-library modules (`copy`, `hashlib`, `hmac`, `math`, `random`, `uuid`, `datetime`, `collections.abc`, `typing`), plus `agent_learning.types` and `.base`. No `agent_learning.storage`, no file I/O, no numpy.
5. **`prng_seed` is a decimal string** in the record (BRU-015-02), so it survives JSON.
6. **Posterior in the snapshot (Story 15.2):** `metadata["posterior_parameters"]` is `{"alpha": {action_id: x}, "beta": {...}}` and `metadata["consumed_episode_ids"]` a list of unique ids. `ThompsonPolicy.from_actions` starts every action at the prior (1.0, 1.0) with empty consumed ids and zero `logits`. `from_snapshot` refuses, with `ValueError` naming the action or id: a value that is not a finite positive number (a `bool` or string counts as not a number), an action outside the action space, a duplicate consumed id, a wrong shape. An action missing from the mapping reads as the prior.
7. **Copies, not references:** the policy keeps a copy of the snapshot it is given and never changes the caller's. `posterior()`, `consumed_episode_ids()` and `snapshot()` return copies; `snapshot()` has every action filled in.
8. **`apply_update` raises `TypeError("use ThompsonLearner")`** (FDD-015 §3 item 5, D6).
9. **`choose(state=None, *, request_id=None, timestamp=None)`** (Story 15.3): a missing id or timestamp is supplied (UUID4, current UTC ISO 8601) and recorded; an explicitly empty one is not "missing" and raises `ValueError` from `seed_for`. The seed is `seed_for(snapshot.id, request_id, timestamp)`; one `betavariate` per action in snapshot order; the highest draw wins and a tie goes to the earlier action. The missing-argument tests use `is None`, never truthiness.
10. **`Decision.logprob` is `None`** for Thompson (`Optional[float]` in `policy/base.py`): there is no selection probability, and a made-up number would let `ReinforceLearner` treat the draw as a softmax sample (FDD-015 D3). `Decision.probabilities` is the normalised posterior mean, for display only, not the selection probability.
11. **`last_sampling_record()`** is `None` before the first `choose`, then a deep copy of the FDD-015 §2.3 record (callers attach it to `Episode.metadata["thompson_sampling"]`); mutating it never reaches the policy. Replay with `replay(record, policy.snapshot().id)`.
12. **Learner (Story 15.4):** `ThompsonLearner.update(policy, episodes, rewards)` needs a `ThompsonPolicy` (`TypeError` otherwise) and writes through `ThompsonPolicy.update_posterior(alpha, beta, consumed_episode_ids, *, episodes_seen)`, which validates before writing and advances the version. `apply_update` stays a `TypeError`.
13. **Scale:** `r = reward_to_success(value) = (value + 1) / 2`; a value that is not finite or lies outside [-1, 1] raises `ValueError`. Every aggregate reward offered is validated, as `ReinforceLearner` does, even one for an episode that is then skipped. The newest aggregate reward per episode wins.
14. **Counted once (D7):** an episode counts only if its `metadata["selection_basis"]` is `"thompson_sampling"`, its `action_id` is in the action space, it has an aggregate reward, and its id is not in `consumed_episode_ids`. The id is added as it is counted, so a repeat in the same call is skipped. An episode with no reward yet is *not* consumed, so a late reward is counted when it first arrives (AC_8). `TrainingRunner` needs no change: it re-offers the latest episodes every run, and the consumed ids make that safe (AC_7).
15. **Ceiling:** after all episodes of a call, any action whose `alpha + beta` exceeds `N_MAX` (5000.0) has both parameters multiplied by `N_MAX / total`; a total at or below `N_MAX` is untouched. A call with no usable episode returns `episodes_used=0`, `consumed_inputs=[]` and does not change the policy, not even its version.
16. **The seed's policy id changes on every update** (`advance_version` gives a new snapshot id, and `seed_for` keys on it). `replay` therefore needs the id the policy had when it drew; keep it with the record (FDD-015 §7 item 6).
17. **Out of REINFORCE (Story 15.5):** a Thompson `Decision.logprob` of `None` reaches `Episode.action_logprob` through `EpisodeCapture.start(action_logprob=decision.logprob)`, and `ReinforceLearner` already skips an episode whose `action_logprob is None` (FDD-015 D6). This epic adds no condition to `learners/reinforce.py`; `tests/test_thompson_reinforce_guard.py` pins the behaviour (a Thompson-only set uses 0 episodes and leaves the logits alone; in a mixed set only the softmax episodes count). It never reads the module's source or the `full_authority_excluded` counter name (FDD-015 §7 item 3 is open), so renaming that counter is not blocked by it. Never give a Thompson `Decision` a made-up log-probability: that is the one thing that would let REINFORCE train on a draw.
