# FDD-021: Contextual Authority Ensemble Routing

**Source ADR:** [ADR-021](../../adr/ADR-021-contextual-authority-ensemble-routing.md) — Accepted (2026-10-28)  
**Source BRD:** [BRD-021](../Business-Requirements/BRD-021-contextual-authority-ensemble-routing.md)  
**Status:** Draft (2026-10-29) — derived from Accepted ADR-021; not yet adjudicated through `approve-fdd`. Section 4 lists where this design departs from ADR-021 §4.1 to §4.5. Menno confirmed the departures K1 to K7 on 2026-10-29 (K1, K4 and K5 as the options recommended in this FDD) and ADR-021 §4.1 to §4.5 were amended to match.  

---

## 1. Architecture & Component Placement

1. **Module** `src/agent_learning/routing.py` holding `RoutingConfig`, `RouteDecision`, `PINNED_FULL`, `route`, `shadow_record`, `previous_route`, `agreement`, `propose_bucket`, `seed_prior` and `policy_for_route`. It uses the standard library, `DecisionAuthority` and `TaskPolicy` from `agent_learning.decision`, `wilson_lower_bound` from `agent_learning.autonomy`, and `Episode` and `PolicySnapshot` from `agent_learning.types`. It imports nothing from `agent_learning.storage`, uses no random number, and does no file I/O. The functions take episodes and snapshots as arguments; a caller reads and writes the store.
2. **One command** in `cli.py`: `task-policy-routing-set` (K4), in the manner of `task-policy-authority-set`. It reads and writes the store.
3. **Two policy shapes** as data files beside the others: `docs/policy-shapes/approve-routing-thresholds.actions.json` and `docs/policy-shapes/approve-routing-bucket.actions.json`, each with the three actions of the other `approve-*` gates (`approve_*`, `reject_*`, `request_revision_before_decision`). Both tasks are pinned (section 3 item 2).
4. **`ReinforceLearner`** gains one condition (K6). It is the only existing module this epic changes.
5. **State.** `PolicySnapshot.metadata["routing_state"]` holds only what a human sets (K1): the thresholds, `max_evidence_age_days`, and the approved buckets with their priors. The per-request state (the previous route of a bucket, the agreement counts) is derived from episodes. A task is routed only if its snapshot carries `routing_state`; a task without it keeps its stored authority.
6. **Package export:** the public names are re-exported from `agent_learning/__init__.py`.

---

## 2. Data Contract

### 2.1 Constants
| Name | Value | Meaning |
|---|---|---|
| `MIN_GAP_BITS` | 0.15 | the smallest allowed `tau_esc - tau_deesc` (ADR-021 Invariant 6) |
| `EPS_MARGIN_DEFAULT` | 0.20 | the default margin threshold (ADR-021 §4.1) |
| `VALID_TIERS` | `low`, `standard`, `high`, `critical` | the autonomy tiers of `config.py`; any other value is invalid input |
| `PINNED_FULL` | `approve-charter`, `approve-adr`, `approve-brd`, `approve-fdd`, `approve-user-stories`, `approve-pmp`, `approve-adaptation-plan`, `approve-subsidiary-plan`, `retrospective`, `approve-routing-thresholds`, `approve-routing-bucket` | the baseline gates of ADR-021 §4.1 and the two decisions this epic adds |
| `SEED_DAMPING_DEFAULT` | 0.70 | the damping of ADR-020 §4.1 |

### 2.2 Dataclasses
```python
@dataclass(frozen=True)
class RoutingConfig:
    tau_esc: float          # entropy at or above this routes full, in bits
    tau_deesc: float        # entropy at or below this may route low, in bits
    eps_margin: float = 0.20
    # __post_init__: ValueError unless all finite, 0 <= tau_deesc, tau_esc - tau_deesc >= 0.15, 0 < eps_margin <= 1

@dataclass(frozen=True)
class RouteDecision:
    authority: DecisionAuthority
    entropy_bits: float | None      # None when the input was invalid
    margin: float | None
    reason: str                     # pinned, critical, entropy, margin, low, not_approved, hysteresis, no_previous, anomaly
    anomaly: str | None
```
`tau_esc` and `tau_deesc` have no default value (ADR-021 §4.1: no calibrated values exist).

### 2.3 Episode metadata of a routed decision
```json
{
  "routed_authority": "full",
  "routing": {"bucket": "ctx-17", "route": "full", "entropy_bits": 1.2955, "margin": 0.3,
              "reason": "entropy", "thresholds": {"tau_esc": 1.0, "tau_deesc": 0.7, "eps_margin": 0.2}},
  "routing_anomaly": null,
  "shadow_low_action": "approve_plan",
  "shadow_entropy_bits": 1.2955
}
```
`routing_anomaly` is present (a string) only when an anomaly occurred. `shadow_low_action` and `shadow_entropy_bits` are present only for full routes. `routing_bucket` is the context key the caller supplies (`routing.bucket`).

### 2.4 Routing state in the snapshot
```json
"routing_state": {
  "thresholds": {"tau_esc": 1.0, "tau_deesc": 0.7, "eps_margin": 0.2},
  "max_evidence_age_days": 30,
  "buckets": {"ctx-17": {"approved": true, "revalidate": false, "approval_episode_id": "...",
                          "approved_at": "2026-10-29T08:00:00+00:00",
                          "prior": {"approve_plan": 0.8889, "reject_plan": -0.2018, "revise_plan": -0.687},
                          "prior_provenance": {"damping": 0.7, "counts": {"approve_plan": 18, "reject_plan": 3, "revise_plan": 1}}}}
}
```
`max_evidence_age_days` is absent until a human sets it. The ids and numbers are placeholders.

---

## 3. Behavior

1. **Signals.** Entropy in bits is `-sum p * log2(p)` over the probabilities (terms with `p = 0` are 0). The margin is the largest probability minus the second largest, with a missing second probability read as 0, so a single-action policy has entropy 0 and margin `p`.
2. **`route(probs, tier, task_id, previous, approved_for_low, requires_human_approval, cfg) -> RouteDecision`.** In this order:
   1. **Pinned.** If `task_id` is in `PINNED_FULL`, or `requires_human_approval` is true, the result is `FULL` with reason `pinned`, whatever the other arguments (BRU-021-02).
   2. **Invalid input.** If `probs` is empty, has a value that is not finite or is negative, does not sum to 1 within 1e-6, or `tier` is not in `VALID_TIERS`, the result is `FULL`, reason `anomaly`, with `anomaly` naming the cause and `entropy_bits` and `margin` of `None` (BRU-021-06).
   3. **Critical.** Tier `critical` gives `FULL`, reason `critical` (BRU-021-01). Only `critical` escalates by tier (K3).
   4. **Escalate.** Entropy at or above `tau_esc` gives `FULL`, reason `entropy`; a margin below `eps_margin` gives `FULL`, reason `margin`.
   5. **De-escalate.** Entropy at or below `tau_deesc` (and the margin at or above `eps_margin`) gives `LOW`, reason `low`, only if `approved_for_low` is true; otherwise `FULL`, reason `not_approved` (BRU-021-05).
   6. **Deadband.** Otherwise the previous route stands: `None` gives `FULL`, reason `no_previous`; `FULL` gives `FULL`; `LOW` gives `LOW` if `approved_for_low` is true, else `FULL` with reason `not_approved` (a revoked bucket falls back at once).
3. **`PINNED_FULL` is asserted:** `route` returns `FULL` for each member under every input, and a test iterates the set.
4. **`shadow_record(low_action_id, entropy_bits) -> dict[str, object]`** returns `{"shadow_low_action": ..., "shadow_entropy_bits": ...}` for a full route (K1). It raises `ValueError` for an empty action id or a non-finite entropy. Nothing reads it as a reward.
5. **`previous_route(episodes, bucket) -> DecisionAuthority | None`** returns the route of the newest episode (by `created_at`) whose `routing.bucket` equals `bucket`, or `None`. It reads at most the episodes passed in; the caller bounds the query (K1).
6. **`agreement(episodes, bucket, now, max_evidence_age_days) -> dict`** counts the scored full-routed episodes of the bucket inside the evidence window. An episode counts when it has `shadow_low_action`, a `feedback_status` of `accepted` or `rejected`, and a final action, which is `correct_action_id` when present and `action_id` otherwise. It returns `n`, `k` (shadow equals final), the final action counts, `modal_action`, the `base_rate` (share of the most frequent final action) and the mean shadow entropy. With `max_evidence_age_days` of `None` it raises `ValueError` (BRU-021-11).
7. **`propose_bucket(agreement_result, cfg_gate) -> dict`** reports `eligible`, `n`, `k`, `wilson_lower`, `base_rate`, `mean_shadow_entropy_bits` and a reason. It is eligible only if `n` is at least the gate's minimum outcomes and `wilson_lower_bound(k, n)` is at least the gate's lower bound; the gate is the `standard` tier of `AutonomyConfig`. The base rate is reported beside the bound and is not a second gate (ADR-021 §4.4).
8. **`seed_prior(counts, action_ids, *, damping=0.70) -> dict[str, float]`** (K5). With `f_a = (n_a + 1) / (N + |A|)` the logit is `damping * (ln f_a - mean over b of ln f_b)`. It raises `ValueError` for `damping` outside (0, 1], a negative count, or an action id missing from `counts` or from `action_ids`.
9. **`policy_for_route(snapshot, authority) -> TaskPolicy`** returns a `TaskPolicy` built from a copy of the snapshot with `metadata["decision_authority"]` set to the route (K2). The stored snapshot is not changed. For a pinned task it raises `ValueError` if asked for `LOW`.
10. **`task-policy-routing-set`** (K4) takes `--agent-id`, `--task-id` and one action:
    - `--set-thresholds JSON --approval-episode ID` writes the thresholds (validated as a `RoutingConfig`) and marks every approved bucket `revalidate: true`, which makes `approved_for_low` false for it until it is approved again (BRU-021-13);
    - `--set-max-evidence-age-days N --approval-episode ID` writes the parameter;
    - `--approve-bucket NAME --approval-episode ID [--damping X]` computes the bucket's `agreement` and `propose_bucket` from the stored episodes, refuses unless the proposal is eligible, and writes the bucket as approved with the `seed_prior` of its final action counts and the provenance;
    - `--revoke-bucket NAME` sets `approved` false.
    Every action except `--revoke-bucket` requires `--approval-episode`: the episode must exist, belong to `approve-routing-thresholds` (for thresholds and age) or `approve-routing-bucket` (for a bucket), and carry `feedback_status` `adjudicated` with `decision_disposition` `accepted`. Otherwise the command exits non-zero and writes nothing. It writes `routing_state` into the active snapshot without changing its id or version, as `task-policy-authority-set` does.
11. **Tagging and exclusion.** The caller records section 2.3 on each routed episode. `ReinforceLearner` skips an episode whose `metadata["routed_authority"]` is `"full"`, counting it with the other excluded episodes; an episode with no tag is handled as before, by the existing skip of an episode with no log-probability (K6).

**Worked checks (arithmetic, to be re-run when built).** Entropy and margin: `[0.95, 0.05]` gives 0.2864 bits and 0.90; `[0.8, 0.2]` gives 0.7219 and 0.60; `[0.5, 0.5]` gives 1.0 and 0.0; the uniform distribution over four actions gives 2.0 and 0.0; `[0.6, 0.3, 0.1]` gives 1.2955 and 0.30; `[0.45, 0.40, 0.15]` gives 1.4577 and 0.05. With `tau_esc = 1.0`, `tau_deesc = 0.7`, `eps_margin = 0.20`, an approved bucket and a standard tier: `[0.95, 0.05]` routes low; `[0.8, 0.2]` (0.7219 bits, inside the deadband) keeps the previous route; `[0.5, 0.5]` routes full; `[0.45, 0.40, 0.15]` routes full by margin; the same `[0.95, 0.05]` for an unapproved bucket routes full. Seeding: final action counts `(18, 3, 1)` give `f = (0.76, 0.16, 0.08)`, base rate 0.8182, and with damping 0.70 the logits `(0.8889, -0.2018, -0.6870)`, and with damping 1.0 `(1.2698, -0.2883, -0.9815)`. The gate: a Wilson lower bound of `k = n = 20` is 0.8389, below 0.90, so 20 perfect agreements do not pass; 34 of 34 gives 0.8985 and 35 of 35 gives 0.9011, so at least 35 agreements without a miss are needed (K7).

---

## 4. Departures from ADR-021 §4.1 to §4.5

Each is a place where ADR-021, as first accepted, did not fit the code that exists today, contradicted itself, or left a gap that code needs closed. Menno confirmed all seven on 2026-10-29 and ADR-021 was amended; the "ADR-021 says" column is the text before that amendment.

| # | ADR-021 says | This FDD does | Why |
|---|---|---|---|
| K1 | `R_previous` is kept per bucket in a bounded least-recently-used map in `PolicySnapshot.metadata["routing_state"]`, with an eviction count; agreement counts are tracked per bucket; `shadow_record(low_action_id, final_action_id, entropy_bits)` | `routing_state` holds only human-set configuration; the previous route and the agreement counts are derived from episodes (`previous_route`, `agreement`); `shadow_record` takes the shadow action and entropy only | Updating a snapshot on every decision means a new stored snapshot or an in-place write per request: version churn, races between concurrent requests, and a pointer write each time. The episode already carries `routed_authority` and the shadow action, and the final action is not known when the decision is made, so it cannot be an argument of a function called then. There is no map to evict. Needs Menno's choice |
| K2 | Route LOW via `TaskPolicy.decide()`, FULL via the resolver; the stored authority is static today | `policy_for_route` builds a `TaskPolicy` from an in-memory copy with the route as its authority; only snapshots with `routing_state` are routed | `TaskPolicy` reads `decision_authority` from the snapshot when constructed and has no per-call override. A copy dispatches without changing the stored policy |
| K3 | "Whether the declared complexity tier is `critical` or high-impact" | Only `critical` escalates by tier, as the rule's formula says; `high` is decided by entropy and margin unless the task requires human approval; an unknown tier is invalid input | The formula names `Tier = Critical` only, "high-impact" is undefined, and `ComplexityProfile.requires_human_approval` already pins the tasks that need it |
| K4 | Thresholds and approvals are "a human decision recorded as an episode (the same `approve-*` pattern)"; no way to apply one is specified | Two approval shapes (`approve-routing-thresholds`, `approve-routing-bucket`) and the command `task-policy-routing-set`, which applies a change only when it cites an adjudicated accepted approval episode of the right task | Without it an approval is a record that changes nothing, or a hand edit of the snapshot. Needs Menno's choice |
| K5 | The bucket prior is "seeded from its observed agreement frequencies, damped as in ADR-020 ... The FDD confirms this mechanism" | `f_a = (n_a + 1) / (N + |A|)` and `logit = damping * (ln f_a - mean ln f)`, damping default 0.70 | The ADR names the inputs but not the formula. The Laplace smoothing keeps an action never seen from getting minus infinity; its strength is a provisional choice with no data behind it. Needs Menno's confirmation |
| K6 | "`LearningRunner` and `ReinforceLearner` skip an episode when `routed_authority == "full"`"; "Dependency that must be built first: ADR-001 §4.5 records that the rule is not enforced in code today" | Only `ReinforceLearner` gains the skip; `LearningRunner` hands it the episodes and is unchanged. The dependency note is corrected: `ReinforceLearner` already skips an episode with no log-probability, which every reasoned (full-authority) decision is, and counts it as excluded; the tag adds an explicit guard | `reinforce.py` already contains the exclusion; what is missing is only the tag check. Stating the dependency as unbuilt is out of date |
| K7 | The agreement gate is "at least 20 outcomes, Wilson lower bound >= 0.90" | The gate is applied as written, and the FDD states that the 20-outcome floor is not binding: a Wilson lower bound of 0.90 needs at least 35 agreements with no miss | The lower bound of 20 of 20 is 0.8389. The same arithmetic applies to the ADR-003 autonomy gate. Stating it prevents a reader expecting a bucket to qualify at 20 |

---

## 5. Error Handling

| Scenario | Behavior |
|---|---|
| `RoutingConfig` with a gap under 0.15 bits, inverted thresholds, a non-finite value or `eps_margin` outside (0, 1] | `ValueError` naming the argument |
| Invalid `probs` or an unknown tier | `FULL` with reason `anomaly`; the caller records `routing_anomaly` |
| A pinned task or `requires_human_approval` | `FULL`, reason `pinned`, for any input |
| `previous` of `None` inside the deadband | `FULL`, reason `no_previous` |
| `approved_for_low` false | never `LOW`; reason `not_approved` |
| `agreement` with `max_evidence_age_days` of `None` | `ValueError`; no bucket can be proposed |
| `propose_bucket` below the gate | `eligible` false with the numbers and the reason |
| `seed_prior` with damping outside (0, 1], a negative count or a missing action | `ValueError` |
| `policy_for_route` asking `LOW` for a pinned task | `ValueError` |
| `task-policy-routing-set` without a valid approval episode, with an ineligible bucket, or with bad thresholds | exits non-zero; nothing written |
| An episode tagged `routed_authority` `"full"` offered to `ReinforceLearner` | skipped and counted as excluded |

---

## 6. Out of Scope

Calibrating the thresholds; router KPIs, a benchmark and named owners; measuring token or latency savings; an LLM router and cascade fallback; wiring the router into `task-policy-decide`; changes to the resolver or the ADR-003 gate.

---

## 7. Decisions and Open Questions

1. **K1 to K7: decided (2026-10-29).** Menno confirmed them and ADR-021 was amended to match. K1 derives the state from episodes, K4 uses the command citing an approval episode, K5 the Laplace-smoothed seed.
2. **Open, and affects earlier epics: the "reinforce.py unchanged" criteria.** Stories 15.5 AC2, 16.5 AC2 and 17.5 AC2 fail if the source of `learners/reinforce.py` differs from the one recorded when the story starts. K6 changes that file in this epic, so building Epic 21 after those epics would fail their tests. Those criteria should become a behavioural check (an episode with no log-probability is skipped) instead of a source comparison.
3. **Open: the routed traffic does not exist.** No policy has run in both modes, no episode has a `routing` record, and no threshold is calibrated. Story 21.7 shows this.
4. **Open: wiring.** `task-policy-decide` dispatches a stored policy's single authority. Calling the router from it, and passing the bucket, is a separate decision.
5. **Open: the agreement count from an untrained low policy** (ADR-021 §4.4). The base rate and the shadow entropy are reported so an approver can see whether agreement exceeds chance; neither is a gate.
6. **Open: the bucket definition.** The caller declares the context key. How a good key is chosen, and how many buckets are practical, is not decided here.
7. **Walkthrough sketch aligned (2026-10-29).** `examples/methodologies/17-authority-routing/sketch.py` had no margin rule, no `approved_for_low`, an incomplete pinned list and no `previous` of `None` case. It now has the margin rule, requires an approved bucket for the low route, pins the full list, and starts a first call inside the deadband on full, as ADR-021 §4.1 says. It is still a sketch, not evidence (ADR-036), and is rewritten against the real module once built.

---

## 8. Test Data

*Real:* none. No episode carries `routed_authority` or a low-policy distribution; the recorded `approve-*` tasks are all pinned and full authority. Story 21.7 shows that every recorded gate routes full. The 14 `approve-adr` episodes carry real `expected_utility` and `robust_utility` (ADR-021 §4.5) but say nothing about entropy. *Gap:* real mixed-difficulty traffic through a hybrid policy, with a context key declared for each request. *Oracle:* the entropy, margin, seeding and Wilson values of section 3, built from constructed distributions and episodes, labelled as arithmetic checks, not as evidence.
