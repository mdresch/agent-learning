# FDD-014: Lightweight Critique-to-Evidence Ingestion

**Source ADR:** [ADR-014](../../adr/ADR-014-critique-to-evidence-ingestion.md) — Accepted (2026-10-28)  
**Source BRD:** [BRD-014](../Business-Requirements/BRD-014-critique-to-evidence-ingestion.md)  
**Status:** Draft (2026-10-28) — derived from Accepted ADR-014; not yet adjudicated through `approve-fdd`. Section 4 lists where this design departs from ADR-014 §4.4; those departures need the maintainer's decision and an ADR-014 amendment before the stories are built.  

---

## 1. Architecture & Component Placement

1. **Pure module**, standard library only, in the style of `review_triage.py`: `src/agent_learning/critique_evidence.py`. It reads the frozen dataclasses of `agent_learning.decision` (`DecisionFrame`, `DecisionOption`, `EvidencePoint`) and nothing from `agent_learning.storage`. No file I/O.
2. **Package export:** public names are re-exported from `agent_learning/__init__.py`.
3. **Resolver untouched.** The module builds a new `DecisionFrame` and hands it to the existing `DecisionResolver`. It does not change how the resolver pools evidence.
4. **Caller owns persistence.** The module returns plain dicts; the caller attaches them to `Episode.metadata["critique_adjustments"]`.

---

## 2. Data Contract

### 2.1 Tag grammar
A finding is one Markdown bullet. Other lines (headings, prose, blanks) are ignored.
```
- [finding: Q-34-1] [criterion: architectural_soundness] -0.20: Unchecked concurrency race on active pointer replace
- [criterion: consequences_honest] +0.10: Explicit disclosure of negative performance trade-offs
```
- `[finding: <id>]` is optional. The id matches `[A-Za-z0-9._-]+`.
- `[criterion: <id>]` is required and matches the criterion ids of the frame.
- The delta is required, with an explicit sign, then a colon.
- The rationale (the rest of the line) must not be empty.

### 2.2 Dataclasses
```python
@dataclass(frozen=True)
class CritiqueDelta:
    criterion_id: str
    support_delta: float        # [-1.0, 1.0]
    rationale: str              # the finding text, kept verbatim
    finding_id: str             # given in the tag, else f"{source_id}#{n}"

@dataclass(frozen=True)
class AppliedCritique:
    frame: DecisionFrame
    adjustments: tuple[dict[str, object], ...]   # one per delta, in the order applied
```
Each adjustment dict holds: `finding_id`, `criterion_id`, `support_delta`, `rationale`, `support_before`, `support_after`, `uncertainty_before`, `uncertainty_after`, `point_support`, `point_confidence`, `kappa`.

### 2.3 Constants
| Name | Value | Meaning |
|---|---|---|
| `KAPPA_DEFAULT` | 0.2 | doubt added per unit of defect delta; allowed range [0.1, 0.5] (ADR-014 §4.1) |
| `CONFIDENCE_FLOOR` | 0.05 | the lowest confidence an appended point may carry; the resolver requires confidence in (0, 1] |
| `TARGET_EPSILON` | 1e-6 | pooled-support targets are clamped to [1e-6, 1 - 1e-6] so the log-odds stay finite |
| `RESOLVER_EPSILON` | 1e-12 | the clamp the resolver applies to each point's support; reproduced here to pool identically |

---

## 3. Behavior

1. **`parse_critique(text, source_id)`** returns the deltas in line order. It raises `ValueError` naming the line number for: a bullet with no criterion tag; a missing, unsigned or non-numeric delta; a delta outside [-1.0, 1.0]; an empty rationale; an invalid finding id; a `source_id` that does not match `[A-Za-z0-9._-]+`. A line that is not a bullet is ignored.
2. **`apply_critique(frame, option_id, deltas, *, kappa=KAPPA_DEFAULT)`** returns an `AppliedCritique` and leaves the input frame unchanged. It validates first (kappa in range; the option exists; every criterion is in the frame; no finding id repeats for one criterion or collides with an existing source). Then, for each delta in order:
   1. Take the option's evidence points on that criterion, including those appended earlier in this call. If there are none, raise `ValueError` (there is nothing to adjust, and no prior is invented).
   2. Pool them exactly as the resolver does: `s = sigmoid(sum(c_i * logit(clamp(p_i))))`, with `clamp` to `[RESOLVER_EPSILON, 1 - RESOLVER_EPSILON]`.
   3. Target: `s_star = clamp(s + delta, TARGET_EPSILON, 1 - TARGET_EPSILON)`.
   4. Doubt: `u = 1 - mean(c_i)`; `u_after = min(1, u + kappa * max(0, -delta))`; the new point's confidence is `c_new = max(1 - u_after, CONFIDENCE_FLOOR)`.
   5. The new point's support is the value that moves the pooled log-odds onto the target: `p_new = sigmoid((logit(s_star) - logit(s)) / c_new)`.
   6. Append `EvidencePoint(criterion_id, f"critique:{finding_id}", p_new, c_new)` and record the adjustment.
3. **`to_episode_metadata(applied)`** returns `{"critique_adjustments": [<adjustment dicts>]}`, JSON-serialisable, imports nothing from `agent_learning.storage`.
4. **Direction and exactness follow from step 5.** The pooled log-odds change by `c_new * logit(p_new) = logit(s_star) - logit(s)`, so the pooled support becomes `s_star` for any `c_new`. A negative delta gives `p_new < 0.5`, a positive delta `p_new > 0.5`, a zero delta `p_new = 0.5`.

**Worked check, run against the real resolver on 2026-10-28.** Points (support 0.8, confidence 0.8) and (0.7, 0.9) pool to 0.8666. A finding with delta -0.20 gives `p_new` = 0.1865 at confidence 0.8, and the pooled support is 0.6666. Deltas -0.20 then -0.10 end at 0.5666. Targets at the edges (delta -0.9 and +0.9) land on 0 and 1 within 1e-6.

---

## 4. Departures from ADR-014 §4.4

ADR-014 is Accepted. These are changes this FDD needs; each needs the maintainer's decision, and an amendment to the ADR if confirmed.

| # | ADR-014 §4.4 says | This FDD does | Why |
|---|---|---|---|
| D1 | Append an `EvidencePoint` whose support is the adjusted support `s'` | Append a point whose support makes the pooled log-odds land on `s'` (§3 step 5) | The resolver adds confidence-weighted log-odds across all points. Run against the real resolver, ADR-014's mechanism turned a -0.20 defect finding into a **+0.052** rise in pooled support (0.8666 to 0.9188). It breaks BRU-014-03 |
| D2 | `parse_critique(text)` | `parse_critique(text, source_id)` | The tag examples in §4.2 carry no finding id, yet Invariant 3 needs one. A source id gives an ordinal id (`<source_id>#<n>`) when the tag has none |
| D3 | `u'` is the doubt a defect adds; the point's confidence is `1 - u'` | Same formula, but its effect is smaller than the ADR implies | The resolver's option uncertainty is the weighted entropy of the pooled support, and the pooled support is pinned to `s'` here. So `u'` changes only the point's weight and `disagreement_bits`, not the option's uncertainty. A defect adds doubt by moving support toward 0.5, as the entropy rises there |
| D4 | `apply_critique` returns a `DecisionFrame`; `to_episode_metadata(deltas)` takes deltas | `apply_critique` returns `AppliedCritique`; `to_episode_metadata(applied)` | The metadata must hold `support_before` and `support_after`, which only exist after applying |
| D5 | Not stated | A criterion with no existing evidence on the option raises | Adjusting nothing would need an invented prior |

---

## 5. Error Handling

| Scenario | Behavior |
|---|---|
| Bullet without `[criterion: ...]` | `ValueError` with the line number; nothing is guessed |
| Delta `-1.20` or `+1.01` | `ValueError`, the bound is [-1.0, 1.0] |
| Delta written without a sign | `ValueError` |
| Criterion not in the frame | `ValueError` naming the criterion |
| Criterion has no evidence on the option | `ValueError` (D5) |
| Same finding id twice for one criterion | `ValueError`, the resolver forbids a duplicate source |
| `kappa` outside [0.1, 0.5] | `ValueError` |
| Delta pushes the target past 0 or 1 | The target is clamped; the pooled support lands within 1e-6 of the edge |
| Input frame is reused after `apply_critique` | Unchanged; the call works on a copy |

---

## 6. Out of Scope

Inferring tags or deltas from free text; the rubric a reviewer uses to choose a delta; changes to the resolver or its pooling; exporting the original Amazon Q comments; running the resolver on the adjusted frame (the caller does that); fine-tuning and reflection loops.

---

## 7. Open Questions (provisional values, for the maintainer)

1. **D1 to D5** above: confirm, and amend ADR-014 §4.1 and §4.4 to match. Until then the stories build the §3 behavior, which is the only one that meets BRU-014-03.
2. **`KAPPA_DEFAULT = 0.2`, `CONFIDENCE_FLOOR = 0.05`, `TARGET_EPSILON = 1e-6`** are starting values.
3. **Do critique points count toward a criterion's `minimum_sources`?** They carry distinct source names, so the resolver counts them. A criterion that lacks independent sources could therefore be satisfied by a reviewer's tag. The default here is that they count; say if they should not.
4. **The delta rubric** is not defined anywhere yet. Without it two reviewers may pick different numbers for the same finding.
