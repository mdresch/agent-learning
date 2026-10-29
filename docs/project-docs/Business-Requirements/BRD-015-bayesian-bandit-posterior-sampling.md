# BRD-015: Bayesian Bandit Posterior Sampling (Thompson Sampling)

**Source ADR:** [ADR-015](../../adr/ADR-015-bayesian-bandit-posterior-sampling.md) — Accepted (2026-10-28)  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Proposed)  
**Status:** Approved (2026-10-29, Menno) — derived from Accepted ADR-015; adjudicated via `approve-brd` (robust utility 0.741, episode `4017d16c-1a58-4337-9db7-c1a037730ead`).  
**Stakeholders:** Menno (Sponsor/PM/maintainer); SDK adopters who run low-authority policies whose history is mostly successes; auditors who replay a decision  

## Business Need

A low-authority policy trained with REINFORCE stops learning when nearly every outcome is a success: the advantage `r - b` goes to zero as the baseline `b` approaches 1.0 (HYP-AL-002). Production histories are skewed this way, because failures are filtered out before they are stored or simply rare. ADR-015 decides a second learner, Thompson sampling over one Beta posterior per action, that keeps explicit uncertainty about each action, so an action with few observations is still tried. Its draws are random, but the repository must be able to replay any decision, so the draw is seeded from the request and recorded. Nothing is built yet.

## Business Rules (BRU)

- **BRU-015-01 (Replayable Draw):** Every decision made by the Thompson policy records the seed, the request id, the timestamp, the posterior parameters it sampled from and the sampled values, in `Episode.metadata["thompson_sampling"]`. Re-deriving the seed and redrawing from the recorded posterior reproduces the recorded vector (ADR-015 §4.3, Invariant 1).
- **BRU-015-02 (Seed Width):** The seed is the first 16 hex digits of an HMAC-SHA256 over the request context, a 64-bit value, stored as a decimal string so that no JSON parser loses its low bits (ADR-015 §4.3, amendment of 2026-10-28).
- **BRU-015-03 (Conjugate Update):** A reward in [0, 1] adds `r` to `alpha` and `1 - r` to `beta` of the chosen action. For a binary reward this is the exact Beta-Bernoulli posterior; for a fractional reward it is a pseudo-count approximation and is documented as such (ADR-015 §4.1).
- **BRU-015-04 (Reward Scale):** The SDK's reward lies in [-1, 1] (`Reward.value`). It is mapped to [0, 1] by `(value + 1) / 2` before the update, and the mapping is stated once, in one place (FDD-015 D1).
- **BRU-015-05 (Effective Sample Size Ceiling):** The total pseudo-count `alpha + beta` of an action never exceeds `N_max = 5000`; a larger total is rescaled so both parameters keep their ratio (ADR-015 §4.1, Invariant 4).
- **BRU-015-06 (Storage Boundary):** Posterior parameters live in `PolicySnapshot.metadata["posterior_parameters"]`. Zero new `LearningStore` record types (ADR-015 Invariant 2; ADR-002).
- **BRU-015-07 (Low Authority Only):** The Thompson policy operates under `DecisionAuthority.LOW`. It never grants autonomy and it never replaces a full-authority resolution (ADR-015 Invariant 3; ADR-001).
- **BRU-015-08 (Stays Out Of REINFORCE):** A Thompson episode never trains `ReinforceLearner`: it carries no behaviour probability, and a REINFORCE update on it would treat the draw as a softmax sample (ADR-015 §4.4; ADR-001 §4.5).
- **BRU-015-09 (No Claim Of Effectiveness):** The first evidence recorded is a consistency check on the recorded positive-only history. It does not claim Thompson sampling decides better than REINFORCE. That needs a low-authority policy with failures, which does not exist (ADR-015 §4.4, test data).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Replay | 100% of tested decisions reproduce their recorded sampled vector from the recorded seed and posterior |
| Seed | the seed is a 64-bit value in a decimal string for 100% of tested decisions; 0 seeds lose bits through `json.dumps` and `json.loads` |
| Update | the update on Beta(1, 1) with r = 1.0 gives (2, 1); closed-form Beta updates match to 1e-12 on every tested case |
| Ceiling | 0 posteriors with `alpha + beta` above 5000 after an update; the `alpha : beta` ratio is kept within 1e-9 |
| Scale | 100% of rewards outside [-1, 1] or non-finite rejected; -1 maps to 0, 0 to 0.5, +1 to 1 |
| Stays out of REINFORCE | 0 Thompson episodes consumed by `ReinforceLearner` |
| HYP-AL-002 check | on the recorded all-ones history (41 episodes when ADR-015 was written; the test records the count it ran on) the posterior of the taken action keeps a standard deviation above 0 and the other actions keep their prior width, while the REINFORCE update on the same history goes to zero |
| Storage boundary | 0 new record types; 0 imports from `agent_learning.storage` in the module |

## Out of Scope

- Showing that Thompson sampling decides better than REINFORCE. It needs a low-authority policy with at least 100 scored episodes that include failures; none exists (ADR-015 §4.4). Recorded as a data gap, not as a story.
- Exponential discounting (`gamma`). ADR-015 §4.1 names it as an alternative to the ceiling; FDD-015 builds the ceiling only (FDD-015 §7, open question 2).
- Contextual or continuous-reward posteriors; the rewards are bounded scalars.
- Priors transferred between policies (ADR-020, HYP-AL-008).
- Changing `ReinforceLearner`'s update, or the full-authority resolver.
