# BRD-006: Opt-In, Lightweight Evidence Capture for `low`-Authority Decisions

**Source ADR:** [ADR-006](../../adr/ADR-006-opt-in-lightweight-evidence-capture-for-low-authority.md) — Accepted (2026-10-23)
**Status:** Draft — business requirements derived from an Accepted ADR
**Stakeholders:** Menno (Sponsor/PM/maintainer)

## Business Need

ADRs 001 through 005 established a strict authority asymmetry: `low`-authority decisions use cheap, non-contextual bandit sampling, whereas `full`-authority decisions perform Bayesian reasoning across a `DecisionFrame`. However, three independent findings converged on a significant evidentiary gap:
1. Historical `low`-authority decisions record no decision rationale (ADR-004 §4.1), rendering them permanently unreplayable and diagnostically opaque.
2. `full`-authority episodes cannot be replayed or mixed into REINFORCE without boundary violations (ADR-001 §4.5).
3. Statistical autonomy-gate tables are inert for `full`-authority decisions (ADR-003 §4.5).

Imposing mandatory `DecisionFrame` capture for all `low`-authority decisions would destroy the cost advantage that justified `low` authority in the first place (ADR-001 §4.1). 

Therefore, a pragmatic, governance-aligned middle ground is required:
- Rich evidence capture is **opt-in per policy**, allowing policy owners to purchase audit and replay depth intentionally.
- The captured payload is **deliberately lightweight** (caller-supplied context, no weighted criteria or Bayes frames).
- The SDK acts strictly as a **transport envelope**, with zero semantic interpretation or learning interference.
- The storage footprint leverages existing metadata extension points (`PolicySnapshot.metadata`, `Episode.metadata`), maintaining the 5-record-type storage boundary (ADR-002 §7).

## Business Rules (BRU)

- **BRU-006-01 (Opt-in by Policy Default False):** Evidence capture must be configurable per policy via `PolicySnapshot.metadata["capture_decision_evidence"]`. It must default to `false`. It is settable only at policy initialization or configuration time, never dynamically during a `decide()` call.
- **BRU-006-02 (Enforced Presence When Enabled):** When `capture_decision_evidence` is `true`, `decide()` on a `low`-authority policy must require non-empty `audit_evidence` (a non-empty `Mapping[str, Any]`). Missing, null, empty, or non-mapping payloads must immediately raise a descriptive `ValueError`.
- **BRU-006-03 (Envelope Non-Interpretation):** The SDK stores and transports `audit_evidence` without validating domain schemas, scoring, or reasoning over its contents.
- **BRU-006-04 (Storage & Lifecycle Immutability):** `audit_evidence` attaches to `DecisionResult` and is persisted into `Episode.metadata["audit_evidence"]`. Once written at decision time, it must be treated as write-once and preserved immutably across episode completion and adjudication lifecycles.
- **BRU-006-05 (Zero Storage Schema Expansion):** No new `LearningStore` container, table, or record type may be introduced. Storage strictly uses existing free-form metadata dictionaries (ADR-002 Invariant #2).
- **BRU-006-06 (Strict Learner Decoupling):** `audit_evidence` is strictly diagnostic telemetry. It must never be consumed by `SoftmaxPolicy.choose()`, reward shaping (`metrics/local.py`), or policy learners (`learners/reinforce.py`). It does not featurize the policy or turn the non-contextual bandit into a contextual model.
- **BRU-006-07 (Non-Retroactivity):** Captured evidence applies strictly forward-looking. Existing historical episodes remain unreplayable without retroactive mutation.

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Zero performance or cost overhead for unopted policies | Unchanged latency and zero evidence requirement when `capture_decision_evidence=false` |
| Deterministic audit trail for opted policies | 100% of decisions under opted policies capture non-empty `audit_evidence` in `DecisionResult` and `Episode.metadata` |
| Zero storage expansion | 0 new Cosmos containers or LearningStore record types introduced |
| Zero learner contamination | 0 references to `audit_evidence` in reward calculators or policy update math |

## Out of Scope

- Mandatory evidence capture across all `low`-authority policies (explicitly rejected in ADR-006 §5).
- Full Bayesian `DecisionFrame` generation for `low`-authority decisions.
- Retroactive backfilling of evidence into historical episodes (ruled out by ADR-004 §4.1).
- Automatic semantic verification or domain-specific schema validation of the audit payload.

