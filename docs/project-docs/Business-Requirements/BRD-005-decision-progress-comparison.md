# BRD-005: Decision-Progress Comparison and Regression Healing

**Source ADR:** [ADR-005](../../adr/ADR-005-decision-progress-comparison.md) — Accepted (2026-10-23)
**Status:** Draft — business rules derived from an Accepted ADR, not yet built
**Stakeholders:** Menno (Sponsor/PM/maintainer). No separate Product Owner exists for this SDK; naming that rather than inventing one.

## Business Need

ADR-005 formalizes a capability this session's own ADR-002 revision pass actually demonstrated it needed: measuring whether a revision to an ADR/BRD/FDD/Story genuinely improved its `approve-*` decision, rather than relying on impression alone. That measurement — `approve_adr`'s robust utility rising from 0.841 to 0.875, margin widening from 0.744 to 0.817 — was real and correct, but was produced entirely by hand: saving one `DecisionResult` JSON file, hand-authoring a second decision-frame, and writing a throwaway Python diff script. Every future revision pass in this governance chain (and every `approve-brd`/`approve-fdd`/`approve-user-stories` decision, not only `approve-adr`) faces the same gap: nothing computes or reports the delta, and nothing guarantees the "before" file survives long enough to compare against.

**This BRD is grounded in real, already-existing data, not a hypothetical.** This session produced real `DecisionResult` files for all four approval policies this repo now has — confirmed on disk:
- `approve-adr`: `adr-001-decision-result.json`, `adr-002-decision-result.json` + `adr-002-decision-result-v2.json` (a genuine two-step revision sequence of the *same* ADR — the real case ADR-005 §4.4 generalizes), `adr-003-decision-result.json`, `adr-004-decision-result.json`, `adr-005-decision-result.json`.
- `approve-brd`: `brd-001-decision-result.json`.
- `approve-fdd`: `fdd-001-decision-result.json`.
- `approve-user-stories`: `epic1-story1-decision-result.json`.

These are the real fixtures FDD-005's contract tests are built against (§ below), not synthetic data invented for this BRD.

## Business Rules (BRU)

- **BRU-005-01**: A comparison must validate that both/all inputs share the same `(agent_id, task_id)`, the same `decision_authority` (`full`), and an identical action taxonomy before computing any delta — mismatching inputs must raise, never silently produce a meaningless number (ADR-005 §4.1, Invariant #2).
- **BRU-005-02**: Every comparison must report a delta for every action in the decision, not only the winning/proposed one (ADR-005 §4.3, Invariant #3).
- **BRU-005-03**: A sequence of more than two results must be classified pairwise, consecutive-step by consecutive-step, using the exhaustive and mutually-exclusive `progression`/`regression`/`flat` taxonomy ADR-005 §4.4 proves — a step's classification is never revised by a later step (Invariant #4/#5).
- **BRU-005-04**: On a `regression` classification, the system must flag it with per-criterion attribution (ADR-005 §4.5 point 1, confirmed real via `OptionAssessment.criteria`), attempt a bounded number of retries, and escalate to human review on exhaustion. It must never generate the corrective revision itself and must never auto-revert any caller-supplied artifact (ADR-005 §4.5 points 4-5, Invariant #6).
- **BRU-005-05**: The capability must remain stateless — no new `LearningStore` record type, no read or write against the store at all (ADR-005 §4.1/§4.2; ADR-002 §7 Invariant #2/#6, which this BRD does not reopen).

## Stakeholder Success Metrics

Named honestly, checkable against real data already on disk:

| Metric | Current state |
|---|---|
| A revision's before/after delta is computed by a reusable function/CLI call, not a one-off script | Not yet true — still ad hoc (this BRD's own motivating evidence) |
| The real `adr-002-decision-result.json` → `adr-002-decision-result-v2.json` pair is correctly classified `progression` (both alternatives fell, leader rose, margin widened 0.744→0.817) | Checkable once built — real, already-produced data, not hypothetical |
| Comparing two unrelated real results (e.g. any `approve-adr` result against `brd-001-decision-result.json`) correctly raises on the `(agent_id, task_id)` mismatch rather than computing a number | Checkable once built — real fixtures already exist for both sides |

## Out of Scope

- Persisting decision-result history as a new `LearningStore` record type — ADR-005 §5 already rejected this.
- The heal step generating the corrective revision itself, or auto-reverting caller content — ADR-005 §4.5 points 4-5 already rejected both.
- The exact CLI surface, retry cap, and tolerance `ε` — real, scoped work for FDD-005, not re-litigated here (ADR-005 §9 already named these as implementation's call).
