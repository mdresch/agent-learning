# Epic 21: Contextual Authority Ensemble Routing

**Source ADR:** [ADR-021](../adr/ADR-021-contextual-authority-ensemble-routing.md) — Accepted (2026-10-28)  
**Source BRD/FDD:** [BRD-021](../project-docs/Business-Requirements/BRD-021-contextual-authority-ensemble-routing.md) / [FDD-021](../project-docs/Functional-Design/FDD-021-contextual-authority-ensemble-routing.md)  
**Status:** Draft (2026-10-29) — stories derived from Accepted ADR-021, BRD-021 and FDD-021; not yet adjudicated through `approve-user-stories`. The epic number follows the source ADR number, as Epic 20 follows ADR-020.  

Seven stories build `src/agent_learning/routing.py`, the command `task-policy-routing-set`, the two approval shapes, and one condition in `ReinforceLearner`. Each rule sits in exactly one story's criteria (LL-012). Contract tests are `tests/test_routing_signals.py` (21.1), `tests/test_routing_route.py` (21.2), `tests/test_routing_pinning.py` (21.3), `tests/test_routing_guard.py` (21.4), `tests/test_routing_decisions.py` (21.5), `tests/test_routing_dispatch.py` (21.6) and `tests/test_routing_real_data.py` (21.7). Calibrating the thresholds, measuring savings and wiring the router into `task-policy-decide` are not stories (BRD-021 Out of Scope).

**Stories 21.1 to 21.7 are unblocked:** Menno confirmed FDD-021 §4 (K1 to K7) on 2026-10-29 and ADR-021 was amended to match. No story depends on another epic, but Story 21.6 changes `learners/reinforce.py`, which conflicts with the source-comparison criteria of Stories 15.5, 16.5 and 17.5 (FDD-021 §7 item 2).

Fixture used by the criteria below ("the base config"): `tau_esc` 1.0, `tau_deesc` 0.7, `eps_margin` 0.20; tier `standard`; task `classify-request` (not pinned); a bucket `ctx-17`. The episodes and snapshots are built in the tests and labelled synthetic.

---

## Story 21.1 — Entropy and Margin

**Status:** Draft  
**As** an auditor, **I want** the two uncertainty signals computed by plain arithmetic, **so that** a route can be checked by hand.

### Acceptance Criteria:
- **$AC_0$ (Entropy In Bits):** entropy is 2.0 for the uniform distribution over four actions, 1.0 for `[0.5, 0.5]`, 0.2864 for `[0.95, 0.05]`, 0.7219 for `[0.8, 0.2]` and 1.4577 for `[0.45, 0.40, 0.15]`, within 1e-4, recomputed in the test from `-sum p log2 p`; a zero probability contributes 0.
- **$AC_1$ (Margin):** the margin is 0.90, 0.60, 0.0, 0.30 and 0.05 for `[0.95, 0.05]`, `[0.8, 0.2]`, `[0.5, 0.5]`, `[0.6, 0.3, 0.1]` and `[0.45, 0.40, 0.15]`; a single-action distribution `[1.0]` has entropy 0 and margin 1.0.
- **$AC_2$ (Pure):** `routing.py` imports nothing from `agent_learning.storage`, no `random` and no `numpy`, and the input sequence is equal to its copy after the call.

---

## Story 21.2 — The Route

**Status:** Draft  
**As** a maintainer, **I want** a request routed by entropy, margin, tier and the bucket's approval, with no flapping, **so that** unsure requests reach full review and routine ones stay fast.

### Acceptance Criteria:
- **$AC_0$ (Config):** `RoutingConfig` raises `ValueError` for a gap under 0.15 bits (including 0.149), for inverted thresholds (`tau_esc < tau_deesc`), for a non-finite value, for a negative `tau_deesc`, and for `eps_margin` of 0 or above 1; a gap of exactly 0.15 is accepted; `tau_esc` and `tau_deesc` have no default.
- **$AC_1$ (Critical):** tier `critical` routes full with reason `critical` for `[0.99, 0.01]` and an approved bucket.
- **$AC_2$ (Escalate):** on the base config entropy at or above 1.0 routes full with reason `entropy`, and a margin below 0.20 routes full with reason `margin`, even when entropy is below `tau_deesc`.
- **$AC_3$ (Earn Low):** with entropy at or below 0.7, margin at or above 0.20 and an approved bucket the route is low with reason `low`; with the bucket not approved it is full with reason `not_approved`, for every entropy.
- **$AC_4$ (Hysteresis):** `[0.8, 0.2]` (0.7219 bits, inside the deadband) keeps the previous route in both directions; a previous low route with the bucket no longer approved gives full with reason `not_approved`; `previous` of `None` inside the deadband gives full with reason `no_previous`.
- **$AC_5$ (No Hunting):** over a sequence of entropies that oscillate inside the deadband the route changes at most once.
- **$AC_6$ (Fail Safe):** an empty list, a NaN, an infinite or negative probability, probabilities summing to 0.9 or 1.1, and an unknown tier each route full with reason `anomaly` and an `anomaly` text naming the cause, and entropy and margin are `None`.

---

## Story 21.3 — Pinned Gates

**Status:** Draft  
**As** an auditor, **I want** the governance gates impossible to route down, **so that** no entropy value can take a human out of a baseline decision.

### Acceptance Criteria:
- **$AC_0$ (The List):** `PINNED_FULL` equals the eleven tasks of FDD-021 §2.1, and the test lists them.
- **$AC_1$ (Always Full):** for each pinned task, over a grid of distributions, tiers, `previous` values and `approved_for_low` values, `route` returns full with reason `pinned`.
- **$AC_2$ (Declared Pin):** a task not in the set, called with `requires_human_approval` true, routes full with reason `pinned`; the same task with false and an approved bucket can route low.
- **$AC_3$ (Pin Beats Invalid Input):** a pinned task with invalid probabilities routes full with reason `pinned`, not `anomaly`.
- **$AC_4$ (Shape Files):** `docs/policy-shapes/approve-routing-thresholds.actions.json` and `approve-routing-bucket.actions.json` each hold the three actions `approve_*`, `reject_*` and `request_revision_before_decision`, and both task ids are in `PINNED_FULL`.

---

## Story 21.4 — The Shadow Record and the Agreement Gate

**Status:** Draft  
**As** an approver, **I want** the evidence that a bucket is ready for the fast path presented with its base rate, **so that** I can see whether the learned policy agrees more than chance.

### Acceptance Criteria:
- **$AC_0$ (Shadow Record):** `shadow_record("a", 1.2955)` returns the shadow action and the entropy as a number; an empty action id or a non-finite entropy raises `ValueError`; the dict contains no reward key.
- **$AC_1$ (Previous Route):** `previous_route` returns the route of the newest episode of the bucket by `created_at`, ignores other buckets and untagged episodes, and returns `None` when there is none.
- **$AC_2$ (Counting):** `agreement` counts only full-routed episodes of the bucket with a shadow action and a `feedback_status` of `accepted` or `rejected`; the final action is `correct_action_id` when present, else `action_id`; episodes outside the evidence window are dropped.
- **$AC_3$ (Fail Closed):** `agreement` with `max_evidence_age_days` of `None` raises `ValueError`.
- **$AC_4$ (Gate Arithmetic):** `propose_bucket` equals `wilson_lower_bound(k, n)` of the counts and compares it with the `standard` tier gate; 20 of 20 gives 0.8389 and is not eligible; 34 of 34 gives 0.8985 and is not eligible; 35 of 35 gives 0.9011 and is eligible; an `n` below the minimum outcomes is not eligible.
- **$AC_5$ (Reported Beside):** the proposal includes `base_rate`, `modal_action`, `n`, `k` and `mean_shadow_entropy_bits`; a bucket where one action is final in 95% of episodes shows base rate 0.95 beside a perfect agreement.
- **$AC_6$ (Never A Reward):** no learner reads `shadow_low_action`; a `ReinforceLearner` run over episodes carrying it gives the same logits as over the same episodes without it.

---

## Story 21.5 — Human Decisions and the Promotion Seed

**Status:** Draft  
**As** a maintainer, **I want** thresholds and bucket approvals to change only through a recorded human decision, **so that** the fast path is never granted silently.

### Acceptance Criteria:
- **$AC_0$ (Seed Arithmetic):** `seed_prior` with counts `(18, 3, 1)` gives `(0.8889, -0.2018, -0.6870)` at damping 0.70 and `(1.2698, -0.2883, -0.9815)` at damping 1.0, within 1e-4; the logits sum to 0; damping of 0, 1.5, a negative count, or a missing action raises `ValueError`.
- **$AC_1$ (Needs An Approval Episode):** every action of `task-policy-routing-set` except `--revoke-bucket` exits non-zero and writes nothing without `--approval-episode`, with an episode that does not exist, belongs to another task, or is not `adjudicated` and `accepted`.
- **$AC_2$ (Approve A Bucket):** `--approve-bucket` with an eligible proposal writes the bucket as approved with the approval episode id, the time, the seed prior and its provenance (damping and counts); with an ineligible proposal, or with `max_evidence_age_days` unset, it exits non-zero and writes nothing.
- **$AC_3$ (Thresholds Revalidate):** `--set-thresholds` writes valid thresholds, rejects an invalid `RoutingConfig`, and marks every approved bucket `revalidate` true, after which the router receives `approved_for_low` false for them until a new approval.
- **$AC_4$ (Revoke):** `--revoke-bucket` sets `approved` false without an approval episode.
- **$AC_5$ (Same Snapshot):** the command changes only `routing_state`, keeping the snapshot id and version; a snapshot without `routing_state` is never routed.
- **$AC_6$ (Seed Not Evidence):** a bucket seeded this way, with no `LOW` episodes of its own, adds no scored outcome to any autonomy gate.

---

## Story 21.6 — Dispatch and Gradient Exclusion

**Status:** Draft — changes `learners/reinforce.py`; see FDD-021 §7 item 2.  
**As** a maintainer, **I want** the chosen route dispatched without touching the stored policy, and full-routed episodes kept out of training, **so that** reasoned decisions never contaminate the learned policy.

### Acceptance Criteria:
- **$AC_0$ (Dispatch):** `policy_for_route(snapshot, LOW)` returns a `TaskPolicy` whose authority is low and `policy_for_route(snapshot, FULL)` one whose authority is full, for the same stored snapshot; the stored snapshot is equal to its copy afterwards.
- **$AC_1$ (Pinned Down-Route Refused):** `policy_for_route` for a pinned task with `LOW` raises `ValueError`.
- **$AC_2$ (Record):** the episode metadata of FDD-021 §2.3 round-trips through `json.dumps` and `json.loads`, holds the route, entropy, margin, reason, thresholds and bucket, and a `routing_anomaly` string only after an anomaly.
- **$AC_3$ (Full Skipped):** `ReinforceLearner.update` over episodes with `routed_authority` `"full"` returns `episodes_used` of 0 for them, counts them as excluded, and leaves the logits unchanged, even when such an episode carries a log-probability.
- **$AC_4$ (Untagged Still Trains):** an untagged episode with a log-probability and a reward is still trained on, and the logits equal those of a run where the full-tagged episodes are absent; an untagged episode with no log-probability is skipped as before.
- **$AC_5$ (Runner Unchanged):** `TrainingRunner` is not modified, and a `run_offline_batch` over a mixed set uses only the low-tagged and untagged episodes with log-probabilities.

---

## Story 21.7 — The Real-Data Check (No Routed Traffic)

**Status:** Draft  
**As** a maintainer, **I want** the router tried against the recorded policies, **so that** the absence of routed traffic and calibrated thresholds is shown, not assumed.

### Acceptance Criteria:
- **$AC_0$ (Real Source):** the policies are the tasks of a temporary copy of the committed store under `data/agent-learning/store`, and the episodes are the committed files in `docs/policy-shapes/episodes/`; the counts and task ids are recorded in the test.
- **$AC_1$ (Gates Route Full):** every recorded `approve-*` task that is in `PINNED_FULL` routes full with reason `pinned` for any distribution, which is the real-data case of Story 21.3.
- **$AC_2$ (No Routed Episodes):** no committed episode carries `routed_authority` or a `routing` record, so `previous_route` is `None` and `agreement` finds no episode for any bucket.
- **$AC_3$ (Nothing Written):** the copy of the store is equal to its earlier state after the checks.
- **$AC_4$ (Labelled):** the result is recorded as a statement that no routed traffic and no calibrated threshold exist yet. It makes no claim about cost or latency (BRU-021-15), and the docstring names the missing data (mixed-difficulty traffic through a hybrid policy with a declared context key per request).
