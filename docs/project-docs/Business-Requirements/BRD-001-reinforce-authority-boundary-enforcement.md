# BRD-001: Enforce the REINFORCE Authority Boundary

**Source ADR:** [ADR-001](../../adr/ADR-001-decision-authority-model.md) — Accepted (2026-10-23)
**Status:** Approved (2026-10-23, Menno) — business rules derived from an Accepted ADR's disclosed gap. Not yet built.
**Stakeholders:** Menno (Sponsor/PM/maintainer). No separate Product Owner exists for this SDK (Project-Charter.md §4's named RACI gap applies here too); naming that rather than inventing one.

## Business Need

ADR-001 formally records a decision that was already believed to be true of the running code: `full`-authority episodes (reasoned, not sampled from the learned policy) are excluded from `ReinforceLearner`'s training updates, because crediting an un-sampled action to the policy's own logits would corrupt the causal link REINFORCE depends on. Writing that decision down and checking it against the actual implementation (ADR-001 §4.5) found the exclusion is not real: a `full`-authority episode with a matching reward enters the gradient step today with full (`iw=1.0`) weight, via `_importance_weight()`'s `None`-fallback. `audit.py` already notices this and emits a warning, but nothing stops it.

The business cost of leaving this unresolved: every organization adopting this SDK's `full` authority route for consequential, human-reviewed decisions is — without being told — also training the bandit on those same decisions' outcomes, silently reintroducing the exact contamination ADR-001 names as unacceptable. The longer this runs unfixed, the more a policy's learned logits are shaped by un-sampled, reasoned actions that were never actually drawn from it — contamination that compounds with every `full`-authority episode and cannot be retroactively un-mixed out of a policy's logits once applied.

## Business Rules (BRU)

- **BRU-001-01**: No episode's outcome may influence `ReinforceLearner`'s gradient update unless that episode's action was actually sampled from the policy being updated (ADR-001 §4.2, §4.5). A `full`-authority episode's `action_logprob` is `None` precisely because no such sampling occurred, and that must be sufficient on its own to exclude it — not merely to zero out its importance-weight reweighting.
- **BRU-001-02**: The exclusion must be enforced where the training batch is assembled or inside `ReinforceLearner` itself — not left to callers to remember to pre-filter, and not left to an audit warning that observes the contamination after the fact without preventing it.
- **BRU-001-03**: This fix must not require a new field on `Episode` if the existing `action_logprob is None` signal is sufficient to identify a `full`-authority episode unambiguously (FDD-001 to confirm this empirically, not assume it).
- **BRU-001-04**: Existing `low`-authority training behavior — including the real importance-sampling case `_importance_weight()` already serves correctly (an episode logged under an older policy version) — must be unchanged. This fix narrows what counts as a trainable episode; it must not change how a trainable episode's weight is computed.

## Stakeholder Success Metrics

Named honestly, not invented ahead of real data:

| Metric | Current state |
|---|---|
| A `full`-authority episode with a matching aggregate reward is excluded from `ReinforceLearner.update()`'s `episodes_used` count | Not yet true — today it is counted and contributes a full-weight gradient term (ADR-001 §4.5) |
| `audit.py:562-563`'s existing warning ("importance weight uses the native fallback of 1") becomes unreachable, because the episode it warns about is excluded before reaching that code path | Not yet true — the warning currently fires because the contamination it describes is real |
| Existing `low`-authority REINFORCE contract tests continue to pass unmodified | Not yet verified against this change — FDD-001/the story's contract must confirm no regression |

## Out of Scope

- Adding a `decision_authority` field to `Episode` or any other storage-schema change, unless FDD-001 finds the existing `action_logprob is None` signal is insufficient to identify the gap unambiguously.
- Any new mechanism for learning from `full`-authority evidence (offline imitation learning, preference modeling, counterfactual evaluation, etc.) — ADR-001 §6 names this as a materially different, future capability, not this fix.
- Re-litigating whether `full`-authority episodes *should* be excluded from REINFORCE — ADR-001 §4.2 already decided that; this BRD only closes the gap between that decision and the code.
