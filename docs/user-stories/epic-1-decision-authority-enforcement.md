# Epic 1: Decision Authority Enforcement

**Source ADR:** [ADR-001](../adr/ADR-001-decision-authority-model.md) — Accepted (2026-10-23), §4.5
**Source BRD/FDD:** [BRD-001](../project-docs/Business-Requirements/BRD-001-reinforce-authority-boundary-enforcement.md) / [FDD-001](../project-docs/Functional-Design/FDD-001-reinforce-authority-boundary-enforcement.md)

One story, matching FDD-001's single design.

## Story 1.1 — Exclude `full`-authority episodes from `ReinforceLearner`'s training batch

**Status:** Completed (2026-10-25) — Implemented via `implement-story` on branch `feat/story-1.1`. Verified with 18/18 tests in `test_learner.py` and 101/101 in `test_audit.py` (442 passed across core suite).
**As** `ReinforceLearner`, **I want** to exclude any episode whose action was not sampled from the policy being updated, **so that** a `full`-authority (reasoned) decision's outcome can never silently train the learned softmax logits it was never drawn from.

**Acceptance Criteria:**
- $AC_0$: `ReinforceLearner.update()`'s per-episode loop skips an episode when `episode.action_logprob is None`, in addition to its existing `action_id` checks — contract-test this directly against a `full`-authority episode (no `action_logprob`) with a matching aggregate reward, asserting it does not appear in `episodes_used` and contributes no gradient delta.
- $AC_1$: `LearnerResult.extra["full_authority_excluded"]` reports the count of episodes excluded for this reason on every call, including when it is `0`.
- $AC_2$: Existing `low`-authority behavior is unchanged — contract-test at least one real importance-sampling case (`action_logprob` set, policy version older than current) still gets reweighted exactly as before, not excluded.
- $AC_3$: `audit.py`'s stale warning ("importance weight uses the native fallback of 1") is replaced with wording that describes exclusion, not reweighting (FDD-001's "Required follow-on") — contract-test the new warning text appears when a `full`-authority episode is present in an audited batch.
- $AC_4$: `audit.py`'s two direct `ReinforceLearner.update()` call sites (`audit.py:444`, `audit.py:503`) require no separate change — contract-test that a replay batch containing a `full`-authority episode excludes it there too, proving the fix is in the right place (the learner, not a single caller).

## Not a story — see ADR-001 §9 Amendment Log

The wording contradiction in ADR-001 §4.3 (reversible vs. one-directional migration) that three independent reviews converged on was fixed directly in the ADR itself, not scoped as code work — it was a documentation defect, not a behavior gap.
