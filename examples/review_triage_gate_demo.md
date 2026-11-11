# AI Code-Review Triage & Calibrated `TaskPolicy` PR Gate — Summary

## Purpose
Demonstrates **Reviewer Reliability Calibration & Evidence-Gated Pull-Request Resolution** (ADR-036 / FDD-036 / ADR-001 / ADR-005). When engineering teams wire automated AI code reviewers (e.g., Amazon Q, Copilot, static bots) into CI/CD pull-request gates, treating every bot comment with a static high confidence creates two operational failure modes:
1. **False-positive fatigue:** A bot with a noisy track record on one claim type (e.g., hallucinated `logic error` claims such as miscounting a 64-character SHA-256 hex digest) blocks clean PRs and forces wasted author rework.
2. **Blind whitelisting:** Disabling or globally down-weighting the reviewer causes the team to miss claim types where that same bot has high verified accuracy (e.g., `crash risk`).

This example shows how to parse structured triage records from `implementation-log.md`, compute a conservative 95% **Wilson score lower bound** per `(reviewer, claim_type)` slice, inject that calibrated confidence into a `FULL`-authority [`TaskPolicy`](../src/agent_learning/decision.py), audit regressions with [`compare_decision_results`](../src/agent_learning/comparison.py), and preserve human triage authority (ADR-003 Invariant 6) through [`TaskPolicy.adjudicate`](../src/agent_learning/decision.py) and [`EpisodeCapture`](../src/agent_learning/capture.py).

File: [review_triage_gate_demo.py](review_triage_gate_demo.py)

---

## Problem Setup
An automated CI governance agent (`ci-governance-agent`) evaluates pull-request merge readiness under task `pr-merge-gate`.

| Element | Definition |
|---|---|
| **Policy Authority** | `DecisionAuthority.FULL` (`TaskPolicy` backed by `DecisionResolver`) |
| **Candidate Actions** | `approve_merge` (merge PR to `main`), `request_author_fix` (block & request remediation), `escalate_human_review` (route to maintainer) |
| **Decision Criteria** | `code_correctness` ($w = 0.65$, `minimum_sources=2`), `ci_verification` ($w = 0.20$), `delivery_velocity` ($w = 0.15$) |
| **Hard Constraints** | `ci_green` and `no_unmitigated_crash_risk` |
| **Calibration Input** | One-line backticked triage records in `implementation-log.md`: ``finding_id | claim type | verified: <v> | decision: <d> | <reason> | fix: <commit or none>`` |
| **Confidence Mapping** | 95% Wilson lower bound (`min_cases=5`) floored at `0.05`; slices with $< 5$ verified cases return `lower_bound=None` and fall back to a cautious unproven prior (`0.25`) |

---

## Core Building Blocks
| Symbol | Module | How the example uses it |
|---|---|---|
| **`find_triage_lines`** / **`parse_triage_line`** | `agent_learning.review_triage` | Extracts and validates historical triage lines (`Q-###-#`) from Markdown logs into immutable `TriageRecord` instances. |
| **`reconstruct_record`** | `agent_learning.review_triage` | Backfills historical review findings from git commit history with `reconstructed=True`. |
| **`reliability`** | `agent_learning.review_triage` | Computes verified counts and the 95% Wilson score lower bound for a specific `(reviewer, claim_type)` slice. |
| **`TaskPolicy`** | `agent_learning.decision` | Evaluates multi-criteria `DecisionFrame` evidence (`decide`) and applies two-step human tie-break dispositions (`adjudicate`). |
| **`compare_decision_results`** | `agent_learning.comparison` | Quantifies the decision-progress delta (`REGRESSION` vs. `PROGRESSION`) and attributes root-cause criterion support drops when uncalibrated confidence overrides Wilson calibration. |
| **`to_episode_metadata`** / **`EpisodeCapture`** | `agent_learning.review_triage` / `agent_learning.capture` | Serializes the human maintainer's triage disposition onto the captured `Episode` in `InMemoryStore` so future calibration rounds incorporate the outcome. |

---

## Walkthrough Flow

1. **Step 1 — Historical Triage Ingestion & Slice Calibration:**
   - Parses 18 historical triage records across PRs `#190`–`#206` (including the real PR `#206` SHA-256 digest false positives `Q-206-1` and `Q-206-2`).
   - Computes per-claim-type Wilson lower bounds for `amazon-q`:
     - `crash risk`: $6/7$ verified ($85.7\%$) $\to$ Wilson LB $= 0.4869$ (`calibrated_conf = 0.4869`)
     - `logic error`: $1/9$ verified ($11.1\%$) $\to$ Wilson LB $= 0.0199$ (`calibrated_conf = 0.0500` floor)
     - `documentation` & `style`: $1/1$ verified ($< 5$ cases) $\to$ `lower_bound = None` (`calibrated_conf = 0.2500` unproven default)
2. **Step 2 — Scenario A vs. Scenario B (Noisy `logic error` Claim on a Clean PR):**
   - **Scenario A (Naive Static Bot Confidence `0.90`):** The bot's false-positive `logic error` claim overwhelms `pytest_suite`, dropping `approve_merge` robust utility to `+0.3315` and falsely selecting `request_author_fix` (`+0.7917`).
   - **Scenario B (Wilson-Calibrated Confidence `0.0500`):** Down-weighting the noisy `logic error` slice to its calibrated confidence preserves the `pytest_suite` + `github_actions_ci` signal. `TaskPolicy.decide()` resolves to `approve_merge` (`+0.6765` vs. `+0.4835`).
   - **Root-Cause Attribution (`compare_decision_results`):** Identifies the naive override as a `REGRESSION` (`leader_changed=True`) and attributes it directly to `code_correctness` support dropping from `0.715` to `0.144` ($-0.571$).
3. **Step 3 — Scenario C (High-Reliability `crash risk` Claim Caught):**
   - On PR `#208`, the same reviewer (`amazon-q`) flags a `crash risk`. Because its `crash risk` Wilson LB is `0.4869` and the unmitigated crash violates `constraint:no_unmitigated_crash_risk`, `approve_merge` is ruled out (`feasible=False`) and `TaskPolicy.decide()` selects `request_author_fix` (`+0.6830`).
4. **Step 4 — Scenario D (Human Tie-Break Adjudication & Episode Lineage):**
   - When an unproven claim slice (`documentation`, `< 5` cases, `conf = 0.25`) lands within a strict margin (`minimum_margin = 0.30`), `TaskPolicy.decide()` returns `NEEDS_USER_TIE_BREAK` with `proposed_action = request_author_fix`.
   - The human maintainer rejects `request_author_fix` (`TieBreakDisposition.REJECT`) and accepts the runner-up `approve_merge` (`TieBreakDisposition.ACCEPT`), producing `authorization_basis = "user_acceptance"`.
   - The new triage record (`Q-207-1`) is serialized via `to_episode_metadata` and persisted onto the captured `Episode`.

---

## Results (Deterministic)

```text
Reviewer Reliability Table (95% Wilson Lower Bound, min_cases=5):
  Reviewer     | Claim Type      | Verified / Cases | Empirical Rate | Wilson LB  | Calibrated Conf
  -------------+-----------------+------------------+----------------+------------+----------------
  amazon-q     | crash risk      | 6 / 7            | 85.7%          | 0.4869     | 0.4869
  amazon-q     | logic error     | 1 / 9            | 11.1%          | 0.0199     | 0.0500
  amazon-q     | documentation   | 1 / 1            | 100.0%         | None (<5)  | 0.2500
  amazon-q     | style           | 1 / 1            | 100.0%         | None (<5)  | 0.2500

Scenario A (Naive Bot Confidence = 0.90 on 'logic error'):
  Status: RESOLVED -> Selected: 'request_author_fix' (robust_utility = +0.7917 vs approve_merge +0.3315)

Scenario B (Wilson-Calibrated Bot Confidence = 0.0500 on 'logic error'):
  Status: RESOLVED -> Selected: 'approve_merge' (robust_utility = +0.6765 vs request_author_fix +0.4835)

Scenario C (Wilson-Calibrated Bot Confidence = 0.4869 on 'crash risk'):
  Status: RESOLVED -> Selected: 'request_author_fix' (approve_merge ruled out by constraint:no_unmitigated_crash_risk)

Scenario D (Unproven Slice Tie-Break -> Human REJECT fix, ACCEPT merge):
  Status: RESOLVED -> Selected: 'approve_merge' (authorization_basis = 'user_acceptance')
```

---

## Key Learnings for Developers
1. **Calibrate per `(reviewer, claim_type)`, never per reviewer globally:** A single AI reviewer can be $85.7\%$ accurate on syntactic/null-safety `crash risk` checks while being $88.9\%$ false-positive on multi-function `logic error` claims.
2. **Never invent reliability from small samples:** Below `min_cases=5`, `reliability()` returns `lower_bound=None` so unproven claim types neither gain false authority nor get silently ignored.
3. **Human triage stays in the loop (ADR-003 Invariant 6):** `review_triage` produces calibrated evidence for `TaskPolicy` and human maintainers; it never auto-dismisses human review or mutates policy weights behind the scenes.

---

## Run It
```powershell
.\.venv\Scripts\python.exe examples/review_triage_gate_demo.py
```
