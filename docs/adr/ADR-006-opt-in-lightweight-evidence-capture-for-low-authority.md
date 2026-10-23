# ADR 006: Opt-In, Lightweight Evidence Capture for `low`-Authority Decisions

## 1. Executive Brief
Three separate ADRs this session independently point at the same root cause from three different angles: ADR-001 §4.5 found `full`-authority episodes aren't properly excluded from REINFORCE; ADR-003 §4.5 found the entire statistical autonomy-gate table is practically inert for `full`-authority policies; ADR-004 §4.1/§4.4 found historical `low`-authority episodes can never be replayed under `full` authority, and explicitly deferred ("not resolved here") the question of mandatory `DecisionFrame`-equivalent capture going forward. All three trace back to one fact: a `low`-authority decision captures almost nothing about *why* it chose an action — not criteria, not options, not constraints, only the sampled logit. This ADR decides how to close that gap **without** repeating ADR-001 §4.1's own cost asymmetry mistake in reverse — by making richer capture **opt-in per policy**, not mandatory for every `low`-authority decision as ADR-004 §4.4 had named as the literal (and explicitly rejected-for-now) option.

## 2. Status
**Accepted (2026-10-23)** — reviewed, refined with code-aligned invariants, and approved by Menno through the real `approve-adr` TaskPolicy governance chain (`task-policy-decide` → Menno's explicit acceptance → `task-policy-adjudicate` → `task-episode-register`). Robust utility: 0.885 vs. 0.041 (reject) and 0.052 (revise).

## 3. Context
- `TaskPolicy.decide()`'s `low` branch (`decision.py:874-928`, specifically 887-895) takes no evidence parameter at all beyond an optional `selected_action_id` — it builds `SoftmaxPolicy.from_snapshot(self.snapshot())` and samples. Confirmed directly (ADR-004 §3): this is a genuinely non-contextual bandit — there is no per-decision reasoning being computed and silently discarded; there is nothing resembling `DecisionFrame` evidence to "capture" from the low path's own math, because the math never produces any.
- `Episode.context_features: Dict[str, Any]` (`types.py:146`) already exists as a field, is already populated by callers today (`capture.py:132/155`), but is **optional**, is **not consumed by `decide()`'s own choice logic** (confirmed, ADR-004 §3), and is used elsewhere only for reward shaping (`metrics/local.py:34-51`). It was never designed to represent "why this action," and mandating it alone would not close the real gap — only give a false sense of replay-readiness.
- `DecisionResult` (`decision.py:316-334`) has no field for arbitrary caller-supplied audit evidence today — confirmed by direct read, same file ADR-005 §3 already characterized as stateless by design.
- `PolicySnapshot.metadata: Dict[str, Any]` (`types.py:395`) already holds `decision_authority` and `complexity_profile` as free-form keys (confirmed ADR-001/ADR-003) — a new key here is a proven, zero-schema-change pattern, not a new mechanism.
- **The real cost tension, named honestly rather than assumed away:** ADR-001 §4.1 built the entire two-route design around `low` authority being cheap — "complexity 5/5, the lowest-cost item in the entire 22-methodology landscape" (per this session's own earlier Business Case work on a related but separate initiative). Requiring every `low`-authority decision to assemble real evidence, even lightweight evidence, adds real cost to the one route that exists specifically to avoid that cost. This ADR's central job is deciding how much of that cost is worth paying, and for whom — not whether evidence capture would be "nice to have," which it obviously would.

## 4. Decision

### 4.1 Evidence capture is opt-in per policy, never mandatory for every `low`-authority decision
A new `capture_decision_evidence: bool` key is added to `PolicySnapshot.metadata`, defaulting to `false` (set at `task-policy-init`/`task-policy-complexity-set` time, the same operator-controlled surface ADR-003 §4.1 already established for `requires_human_approval` and the complexity profile — never settable by the decision call itself). **This is a deliberate narrowing of ADR-004 §4.4's literal option**, which named mandatory capture "for every decision" as the thing being deferred. Mandatory-for-everyone is rejected here (§5); opt-in-per-policy is adopted instead, so a policy owner who genuinely wants future replay/audit depth can pay for it explicitly, while every other policy's `low`-authority cost stays exactly what it is today.

### 4.2 The captured shape is deliberately lighter than a full `DecisionFrame`
When `capture_decision_evidence` is `true`, `decide()`'s `low` branch requires a new, optional-except-when-required keyword argument — `audit_evidence: Mapping[str, Any] | None = None` — and raises `ValueError` if it is `None` or not a non-empty mapping (`not isinstance(audit_evidence, Mapping) or len(audit_evidence) == 0`) while the flag is set (mirroring `decide()`'s existing enforcement style for `full` authority's own frame requirement, §3). **This is not a `DecisionFrame`.** It carries no `DecisionCriterion` weights, no `EvidencePoint`s, no constraints — just a free-form, caller-supplied record of the context that led to this call (e.g., `{"reason": "...", "candidate_actions_considered": [...], "why_this_one": "..."}`), shaped and scoped fully by FDD-level work, not by this ADR. Requiring the full Bayesian evidence shape even for an opted-in `low` policy would just relocate `full` authority's cost onto `low` authority for policies that chose to opt in — defeating the asymmetry for exactly the policies that still need it least.

**SDK Non-Interpretation Boundary:** The SDK acts strictly as a transport and storage envelope for `audit_evidence`. The SDK does not interpret, validate against domain schemas, score, or reason over its contents.

### 4.3 Captured evidence attaches to the `Episode`, not to a new record type
`audit_evidence`, when provided, is attached to the resulting `DecisionResult` (a new field — `DecisionResult` is already stateless and uncomplicated by this, per ADR-005 §3) and, when the caller registers an `Episode`, copied into `Episode.metadata["audit_evidence"]` (an existing, free-form field — `types.py:153`). No sixth `LearningStore` record type, no new container, no change to any of the five record types ADR-002 §4.1/§7 Invariant #2 already fixed.

**Lifecycle Immutability Invariant:** While `LearningStore.store_episode` supports upserts across the episode lifecycle (e.g., updating an incomplete episode when execution outcomes or adjudications arrive via `cli.py`/`capture.py`), `DecisionResult` is frozen at decision time, and its captured `audit_evidence` payload represents decision-time context. Once written to `Episode.metadata["audit_evidence"]`, subsequent episode outcome completion or adjudication passes MUST treat `audit_evidence` as write-once and preserve it without mutation.

### 4.4 This ADR starts the clock; it does not retroactively fix anything
Per ADR-004 §4.1 (still true, not reopened here): episodes logged before this capability exists remain permanently unreplayable — no amount of future tooling recovers evidence that was never captured. This ADR only means that, going forward, a policy owner can opt a specific policy into capturing it. Whether and how to actually build ADR-004 §4.4's deferred retroactive-recalculation loop against these newly-captured episodes is still separate, scoped future work, not resolved by opting a policy in today.

### 4.5 This does not, by itself, answer ADR-003 §4.5's named future question
ADR-003 §4.5 asked whether `full`-authority policies warrant their own distinct autonomy-governance mechanism, since the existing statistical gate table is inert for them. This ADR removes a *different* blocker — the evidentiary gap for `low`-authority replay — and does not touch that question at all. Naming this explicitly so the two are not conflated: closing this gap does not imply or require an answer to that one.

### 4.6 Strict decoupling from policy learning and optimization
`audit_evidence` is strictly audit telemetry. It is completely excluded from policy action selection (`SoftmaxPolicy.choose()`), reward shaping (`metrics/local.py`), and learner optimization (`learners/reinforce.py`). It does not featurize the policy or convert the non-contextual bandit into a contextual model. Any future initiative to use decision context for learning or bandit featurization would represent a fundamental architectural change requiring its own dedicated ADR.

## 5. Alternatives Considered

| Alternative | Reason for rejection |
|---|---|
| Mandatory `DecisionFrame`-equivalent capture for every `low`-authority decision (ADR-004 §4.4's literal, explicitly-deferred option) | Forces real cost onto every policy regardless of whether anyone asked for replay depth, directly eroding the cost asymmetry ADR-001 §4.1 built the two-route design around. Rejected for the same reason ADR-004 deferred it, now resolved as "no, not mandatory" rather than left open. |
| Require the full `DecisionFrame` shape (weighted criteria, `EvidencePoint`s, constraints) even for opted-in policies | Relocates `full` authority's own assembly cost onto `low` authority for the policies that opted in — the asymmetry ADR-001 §4.1 protects should still hold for `low` policies that chose richer capture, just not at `full`-authority's full cost. |
| Mandate populating the existing `context_features` field as the sole mechanism, add nothing new | Nearly free (reuses an existing field), but `context_features` was never meant to represent "why this action" (§3) — mandating it alone would create a false appearance of replay-readiness without the per-decision reasoning a real audit trail needs. Recommended as a complementary, always-on baseline (§6), not adopted as the only mechanism. |
| Do nothing — leave the gap as three separately-named but unaddressed findings | The status quo. Rejected because three independent ADRs this session converged on this same root cause from different angles — a strong, real signal this is a recurring pain point, not a hypothetical one worth deferring indefinitely. |

## 6. Consequences

### Positive
- Gives policy owners a real, explicit lever for future replay/audit depth without taxing every `low`-authority decision for it — the asymmetry ADR-001 §4.1 built this session's whole authority model around stays intact for every policy that doesn't opt in.
- Reuses proven, zero-schema-change patterns throughout (`PolicySnapshot.metadata`, `Episode.metadata`) rather than introducing new persisted state — consistent with ADR-002 §4.1/§4.6/§7's narrow-store discipline.
- Starts the clock honestly (§4.4) rather than implying retroactive repair that ADR-004 §4.1 already ruled out.

### Negative
- Policies that don't opt in gain nothing — the vast majority of this gap (every already-logged episode, and every future episode under a policy that stays opted out) remains exactly as unaddressed as before this ADR. This is a real, partial fix, not a complete one, named as such rather than oversold.
- `audit_evidence`'s free-form shape (§4.2), while cheaper than a full `DecisionFrame`, is unstructured beyond the structural requirement of being a non-empty mapping (`len(audit_evidence) > 0`). Nothing in the SDK enforces semantic quality or deep reasoning within the payload — a caller could pass trivial metadata and still satisfy the structural check. This ADR does not solve semantic quality; that is an intentional limit of keeping the shape lightweight rather than schema-enforced.
- Recommending `context_features` as an always-on baseline (§5) without making it structurally required (only "recommended") means that baseline itself could still be skipped by a caller who doesn't bother — this ADR stops short of hardening that, leaving it as guidance, not enforcement.

## 7. Architectural Invariants

1. `capture_decision_evidence` defaults to `false` for every policy; a policy owner must explicitly opt in via `task-policy-init`/`task-policy-complexity-set`, never implicitly or via the decision call itself (§4.1).
2. When `capture_decision_evidence` is `true`, `decide()`'s `low` branch raises if `audit_evidence` is `None` or not a non-empty mapping (`not isinstance(audit_evidence, Mapping) or len(audit_evidence) == 0`) (§4.2).
3. `audit_evidence` is never a `DecisionFrame`, and the SDK acts strictly as a transport envelope without interpreting, parsing, or scoring its contents — domain scoping belongs strictly to FDD-level work (§4.2).
4. Captured evidence lives in `DecisionResult` and `Episode.metadata["audit_evidence"]`; it is write-once across the episode completion lifecycle (§4.3) and never becomes a sixth `LearningStore` record type (ADR-002 §7 Invariant #2).
5. `audit_evidence` is strictly decoupled from learning and optimization — it is never consumed by `SoftmaxPolicy.choose()`, reward shaping (`metrics/local.py`), or REINFORCE (`learners/reinforce.py`) (§4.6).
6. This ADR does not retroactively apply to any episode logged before the capability exists (§4.4; ADR-004 §4.1 unchanged) and does not itself resolve ADR-003 §4.5's full-authority-governance question (§4.5).

## 8. References
- [`decision.py`](../../src/agent_learning/decision.py) — `TaskPolicy.decide()` (874-928), `DecisionResult` (316-334)
- [`types.py`](../../src/agent_learning/types.py) — `PolicySnapshot.metadata` (395), `Episode.metadata`/`Episode.context_features` (146/153)
- [`capture.py`](../../src/agent_learning/capture.py) — where `context_features` is populated today (132/155)
- [`metrics/local.py`](../../src/agent_learning/metrics/local.py) — where `context_features` is consumed (reward shaping, 34-51)
- [`learners/reinforce.py`](../../src/agent_learning/learners/reinforce.py) — learning loop demonstrating non-interference (§4.6)
- [`storage/base.py`](../../src/agent_learning/storage/base.py) — `LearningStore` five-record boundary (§4.3)
- Related: [ADR-001](./ADR-001-decision-authority-model.md) §4.1 — the cost asymmetry this ADR is built to preserve, not erode
- Related: [ADR-002](./ADR-002-storage-backend-strategy.md) §4.1/§4.6/§7 Invariant #2 — the five-record-type boundary §4.3 preserves
- Related: [ADR-003](./ADR-003-evidence-gated-autonomy-thresholds.md) §4.5 — the full-authority-governance question this ADR explicitly does not resolve
- Related: [ADR-004](./ADR-004-authority-migration-comparison-not-replay.md) §4.1/§4.4 — the deferred mandatory-capture option this ADR resolves as opt-in instead

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-23 | Drafted, Proposed | Initial record of a pattern noticed across three independent ADRs (001 §4.5, 003 §4.5, 004 §4.1/§4.4) rather than one isolated finding, resolving ADR-004 §4.4's deferred "mandatory capture" question as opt-in-per-policy instead |
| 2026-10-23 | Amended (Code-Aligned Review) | Added SDK non-interpretation boundary (§4.2), non-empty mapping structural requirement (§4.2), write-once lifecycle invariant (§4.3), and strict learner/optimizer decoupling (§4.6, §7 Invariant #5) |
| 2026-10-23 | Accepted | Approved by Menno via `approve-adr` governance chain (robust utility 0.885, episode `3d45c90a-3768-46ad-a301-edb00f3908c2`) |
