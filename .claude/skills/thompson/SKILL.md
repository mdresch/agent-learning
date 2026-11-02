---
name: thompson
description: Guidance for Thompson sampling (Beta-Bernoulli posterior, seeded and replayable draws) in agent-learning (ADR-015, Epic 15).
---

# Skill: thompson (agent-learning)

## Overview
Thompson sampling picks an action by drawing one value per action from its Beta posterior and taking the highest draw. The posterior lives in `PolicySnapshot.metadata`; no new record type exists (ADR-002). This skill covers `src/agent_learning/policy/thompson.py` (and, as the stories land, `src/agent_learning/learners/thompson.py`).

## Governing Specifications & Contracts
- **Architecture:** [`docs/adr/ADR-015-bayesian-bandit-posterior-sampling.md`](../../docs/adr/ADR-015-bayesian-bandit-posterior-sampling.md)
- **Business Requirements:** [`docs/project-docs/Business-Requirements/BRD-015-bayesian-bandit-posterior-sampling.md`](../../docs/project-docs/Business-Requirements/BRD-015-bayesian-bandit-posterior-sampling.md)
- **Functional Design:** [`docs/project-docs/Functional-Design/FDD-015-bayesian-bandit-posterior-sampling.md`](../../docs/project-docs/Functional-Design/FDD-015-bayesian-bandit-posterior-sampling.md)
- **User Stories:** [`docs/user-stories/epic-15-bayesian-bandit-posterior-sampling.md`](../../docs/user-stories/epic-15-bayesian-bandit-posterior-sampling.md)
- **Test Contracts:**
  - `tests/test_thompson_seed.py` (Story 15.1: seed and replay)

## Load-Bearing Constraints & Invariants
1. **Seed:** `seed_for(policy_id, request_id, timestamp)` is `int(HMAC-SHA256(key=policy_id, msg=request_id + "|" + timestamp).hexdigest()[:16], 16)`. The `"|"` separator is fixed so `("ab", "c")` and `("a", "bc")` differ. An empty argument raises `ValueError` naming it.
2. **Replay:** `replay(record, policy_id)` re-derives the seed, redraws from the recorded posterior in the order of its `alpha` keys, and returns the redraw. A seed mismatch raises `ValueError` ("seed"); a redraw that differs from `sampled_payoffs` raises `ValueError` ("version"): CPython does not promise the same Beta stream across versions, so that is a version difference, not tampering (FDD-015 §7 item 4). It never reads the store and never mutates the record.
3. **`replay` takes the policy id** because the FDD-015 §2.3 record does not hold it (interpretation I2, FDD-015 §7 item 6).
4. **Purity:** the module imports only `hashlib`, `hmac`, `random` and `math` from the standard library, plus `agent_learning.types`. No `agent_learning.storage`, no file I/O, no numpy.
5. **`prng_seed` is a decimal string** in the record (BRU-015-02), so it survives JSON.
