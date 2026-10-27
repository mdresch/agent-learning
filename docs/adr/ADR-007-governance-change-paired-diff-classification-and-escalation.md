# ADR 007: Automated Governance Change — Paired Diff Classification and Escalation Pipeline

## 1. Executive Brief

On the 18-stage Intent-to-Outcome Chain (`PROJECT-MANAGEMENT-ONTOLOGY.json`), Stage 16 (**Governance Change**) governs the formal amendment or evolution of governance policies and architectural baselines resulting from validated lessons (Stage 15) before downstream execution adapts (Stage 17). Today, evolving an already-accepted governance artifact (an ADR, BRD, FDD, or Story) presents a dangerous dilemma: a trivial erratum or parameter tweak requires manual human bureaucracy, while a disguised, consequential reversal of an architectural decision can slip through under the guise of a "minor clarification."

This ADR establishes an automated, evidence-driven **Governance Change** pipeline powered by two paired `TaskPolicy` instances:
1. **`classify-diff-type`** (`full` authority, Bayesian multi-criteria reasoning): Inspects the semantic diff between a candidate amendment and the frozen accepted baseline to categorize the exact structural *form* of change across a proven 7-action taxonomy grouped into three operational tiers.
2. **`escalate-diff-response`** (`low` authority, learned `SoftmaxPolicy` bandit): Decides whether that classified diff category warrants human escalation, notification, or autonomous application with mandatory audit logging, earning autonomy over time via REINFORCE from downstream outcome rewards.

This pipeline formally closes the development lifecycle loop between Lessons Learned and Workflow Adaptation. It integrates directly with **ADR-005** (verifying that the applied change yields measured decision `progression` rather than `regression`) and **ADR-006** (transporting diff classification context via lightweight `audit_evidence` into the low-authority escalation decision) while strictly preserving ADR-001's authority model and ADR-002's five-record-type storage boundary.

## 2. Status

**Accepted (2026-10-23)** — formally evaluated and approved through the `agent-learning-governance` / `approve-adr` TaskPolicy chain (Episode `9662b831-3a88-4fb9-803b-ed8adde534bf`, robust utility 0.849 vs. 0.043 [reject] and 0.078 [revise]); adjudicated and signed off by Menno Drescher.

## 3. Context

- **The Missing Link on the Cognition Loop:** The repository's Intent-to-Outcome coverage maps 18 stages from Intent to Intent Refinement. Prior to this ADR, `agent_learning` policies existed for Stage 7 Requirement Approvals (`approve-adr`, `approve-brd`, etc.), Stage 8 Gating (`validate-intent-foundation`), and Stage 14/15 Knowledge Synthesis (`resolve-kb-conflict`). Stage 16 (**Governance Change**) and Stage 17 (**Adaptation**) remained unmechanized.
- **The Asymmetry of Diff Risks:** 
  - *Risk A (Disguised Decision Reversal):* A human or agent submits a diff labeled "minor wording cleanup" that secretly removes a critical constraint or flips an architectural trade-off (tested and validated this session: a red-team case attempting to delete an ADR-002 §4.6 citation).
  - *Risk B (Governance Gridlock):* Trivial typo fixes, provenance updates, or parameter adjustments (such as ADR-0017-19) require the full overhead of authoring a new ADR from scratch.
  - *Risk C (False Confidence):* Ambiguous edits close to the boundary between a clarification and an erratum must not pick a side arbitrarily (validated in ADR-0145: produced `needs_user_tie_break` between `correction_note` [0.214] and `clarification_section` [0.195]).
- **Feasibility & Value Hypotheses Already Grounded:**
  - **HYP-AL-006 (Validated):** Confirmed that treating the last accepted artifact as a frozen baseline and evaluating only what *changed* via a full-authority `DecisionFrame` correctly distinguishes genuine decision-changes from amendments across three real test cases.
  - **HYP-AL-007 (Formulated):** Postulates that whether a classified diff-type category typically warrants human escalation is a stable, repeated question that a `low`-authority bandit can learn from aggregate outcomes, unlike the per-instance semantic diff inspection itself.
- **Synergy with ADR-005 and ADR-006:**
  - ADR-005 provides `compare_decision_results()`: once a governance change is applied, re-running the approval decision verifies whether the change produced `progression` or `regression`.
  - ADR-006 provides `audit_evidence`: the full-authority diff verdict can be transported into the low-authority escalation bandit without featurizing the bandit or adding new storage records.

## 4. Decision

### 4.1 Paired Pipeline Architecture: Full-Authority Classification + Low-Authority Escalation

Governance change is partitioned into two distinct, decoupled decision boundaries:

```
Candidate Diff (Candidate vs. Frozen Baseline)
                     │
                     ▼
  ┌─────────────────────────────────────────────────────────┐
  │ 1. classify-diff-type                                   │
  │    Authority: FULL (Bayesian DecisionResolver)          │
  │    Output: Structural Form of Change (7 actions)        │
  └─────────────────────────────────────────────────────────┘
                     │ Selected Diff Type (via audit_evidence)
                     ▼
  ┌─────────────────────────────────────────────────────────┐
  │ 2. escalate-diff-response                               │
  │    Authority: LOW (Softmax Bandit + REINFORCE)          │
  │    Output: Escalation Disposition (3 actions)           │
  └─────────────────────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
   [escalate]    [notify]     [apply]
```

1. **Per-Instance Reasoning (`classify-diff-type`):** Must be `full` authority. Semantic diff inspection cannot be learned by a fixed global bandit because every textual diff introduces novel phrasing, domain concepts, and architectural trade-offs.
2. **Category-Level Policy Learning (`escalate-diff-response`):** Must be `low` authority. Once the diff is classified into a stable category (e.g., `correction_note` vs `new_superseding_adr`), the decision of whether the organization allows autonomous application or mandates human approval is a repeated operational policy that earns autonomy through feedback.

### 4.2 Grouped Classification Taxonomy & Confidence Thresholds (`classify-diff-type`)

`classify-diff-type` evaluates a `DecisionFrame` constructed from the candidate diff against 7 mutually exclusive actions grouped into three operational tiers:

#### Tier 1: Substantive Governance Change
1. `new_superseding_adr`: The diff alters core architecture, reverses previous decisions, or changes system topology $\rightarrow$ mandates drafting a full superseding ADR.
2. `amendment_log_entry`: The diff updates operational parameters, timeouts, thresholds, or implementation facts while preserving core architectural intent $\rightarrow$ appended to the existing ADR's amendment table.

#### Tier 2: Documentation & Clarification
3. `correction_note`: Errata, broken citations, typographical errors, or non-semantic formatting fixes.
4. `clarification_section`: Additional explanatory prose or diagrams addressing ambiguity without altering the decision boundary.
5. `provenance_note`: Lineage, authorship, or upstream specification references updated.

#### Tier 3: Lifecycle Status Mutation
6. `pending_supersession_note`: Flagged on an active artifact indicating a replacement is currently in draft.
7. `supersession_update`: Status transition updating an older artifact once its replacement is formally accepted.

#### Decision Frame Criteria & Weights
- **`semantic_scope_impact` (Weight: 0.40):** Measures whether the diff alters the fundamental decision boundaries or just operational parameters.
- **`architectural_intent_shift` (Weight: 0.35):** Measures whether the diff alters the underlying "Why", principles, or trade-offs.
- **`downstream_contract_footprint` (Weight: 0.15):** Measures whether existing contract tests, interfaces, or consumer expectations are invalidated.
- **`textual_cosmetic_ratio` (Weight: 0.10):** Measures the ratio of substantive structural change to formatting/wording cleanup.

#### Native Utility Margin & Tie-Break Enforcement
To prevent false-confident decisions when evidence is ambiguous, `classify-diff-type` strictly relies on the SDK's native `DecisionFrame.minimum_margin` parameter (`decision.py:142`, default `0.05`):
$$\Delta \text{utility} = \text{robust\_utility}(\text{best}) - \text{robust\_utility}(\text{candidate}_i) \le \text{minimum\_margin} + \epsilon$$
When two or more viable actions fall within this margin, `DecisionResolver` natively yields `DecisionStatus.NEEDS_USER_TIE_BREAK`. Per §7 Invariant #3, this condition triggers an immediate halt and human escalation.

### 4.3 The 3-Action Escalation Policy (`escalate-diff-response`)

`escalate-diff-response` operates as a discrete 3-action `SoftmaxPolicy`:
1. `escalate_to_human`: Halts execution, blocks automated merging, and prompts a human maintainer for sign-off.
2. `apply_with_notification`: Automatically applies the change to the repository, emits an immutable audit event (`Episode`), and sends a notification.
3. `apply_automatically`: Automatically applies the change and commits directly, with mandatory emission of an immutable audit event (`Episode`). No governance update is ever applied silently without audit telemetry.

#### Permanent Lineage Freeze (Autonomy Exclusions)
To protect governance lineage from corruption, the following actions are permanently barred from autonomous application:
- `new_superseding_adr`
- `pending_supersession_note`
- `supersession_update`
These three actions directly alter artifact lifecycle status and governance lineage. They are hard-constrained to require human authorization (`escalate_to_human`). Only Tier 2 documentation changes (`correction_note`, `clarification_section`, `provenance_note`) and parameter adjustments (`amendment_log_entry`) are eligible to earn statistical autonomy over time.

#### Autonomy & Reward Shaping
- Initial state: Initialized with `requires_human_approval: true` on `standard` complexity tier.
- Positive Reward (+1.0): Human accepts the disposition, downstream contract tests pass, and ADR-005 verification confirms `progression`.
- Negative Penalty (-1.0 to -2.0): Human rejects or reverts the autonomous application, or downstream verification detects `regression`.
- Autonomy Progression: As positive evidence accumulates, eligible low-risk categories cross autonomy thresholds, allowing safe autonomous baseline maintenance while high-risk categories remain locked.

### 4.4 Verification and Adaptation Linkage (ADR-005 & ADR-006 Integration)

1. **Transport via ADR-006 (`audit_evidence`):** The output of `classify-diff-type` (selected action, robust utility margin, criteria assessment summary) is passed directly as the `audit_evidence` parameter to `escalate-diff-response.decide()`. In accordance with ADR-006 §4.2, the SDK acts strictly as a transport envelope—it does not featurize the bandit or parse domain schemas.
2. **Verification via ADR-005 (`compare_decision_results`):** After a governance change is applied, the governing approval policy (e.g. `approve-adr`) is re-evaluated against the candidate. `compare_decision_results()` compares the pre-change decision against the post-change decision:
   - If classified as `progression`: Governance change is validated; positive reward is emitted to `escalate-diff-response`.
   - If classified as `regression`: Governance change triggers ADR-005 regression healing (per-criterion attribution, bounded retries, escalation to human).

### 4.5 Scope Boundary: Stage 16 Termination vs. Stage 17 Adaptation

**Explicit Boundary Rule:** ADR-007 terminates with a formally validated, immutable governance baseline. Execution adaptation mechanisms (e.g., executing code amendments, re-running test suites, updating agent system prompts, or altering operational workflows) remain strictly the responsibility of **Stage 17 (Adaptation)**. ADR-007 is a governance change control engine, not an execution runtime.

### 4.6 Classification Safety Test Suite (Adversarial Diff Verification)

To guarantee that `classify-diff-type` cannot be tricked by disguised changes, implementation contracts must validate against an adversarial test suite containing:
1. **Deleted Constraints:** Diff quietly deletes a constraint clause (e.g. removing ADR-002 §4.6 citation) $\rightarrow$ MUST classify as `new_superseding_adr` or fail validation.
2. **Inverted Logic:** Diff negates a condition or flips an inequality sign $\rightarrow$ MUST classify as `new_superseding_adr`.
3. **Removed Guardrails:** Diff removes an error-handling precondition $\rightarrow$ MUST classify as `new_superseding_adr`.
4. **Softened Modal Verbs:** Diff changes normative `MUST`/`SHALL` language to advisory `SHOULD`/`MAY` $\rightarrow$ MUST classify as `new_superseding_adr` or trigger tie-break.
5. **Legitimate Erratum:** Diff fixes typos or citation links without altering semantics $\rightarrow$ MUST classify as `correction_note`.
6. **Parameter Shift:** Diff tunes a numeric threshold while preserving rationale $\rightarrow$ MUST classify as `amendment_log_entry`.

## 5. Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| Single monolithic full-authority policy for classification and escalation | Violates separation of concerns. While diff classification requires per-instance semantic reasoning, escalation disposition is an organizational policy that benefits from empirical learning and statistical autonomy gates. |
| Single low-authority bandit taking raw diff text | Impossible under current SDK architecture. Non-contextual bandits cannot featurize or reason over unbounded textual diffs, leading to random sampling or unlearnable entropy collapse. |
| Heuristic / regex-based diff categorizer | Fragile and easily bypassed by adversarial or subtle red-team diffs (e.g., disguising a decision reversal as a one-line wording change). Lacks Bayesian confidence bounds and tie-break escalation. |
| Full manual human review for all governance edits | The status quo. Causes severe governance bottleneck, discouraging continuous maintenance of live ADRs and leading to stale baselines. |

## 6. Consequences

### Positive
- **Closes the Cognition Loop:** Bridges Stage 15 (Lessons Learned) and Stage 17 (Adaptation) on the 18-stage Intent-to-Outcome chain.
- **Defends Architectural Baselines:** Formally prevents disguised decision changes from bypassing governance scrutiny through adversarial test coverage.
- **Eliminates Bureaucracy for Low-Risk Maintenance:** Allows safe errata, citation fixes, and parameter logs to be processed autonomously as confidence builds.
- **End-to-End Verification:** Guarantees that no governance change takes permanent effect without passing ADR-005 progression comparison against its prior baseline.

### Negative
- **Two Decisions per Governance Event:** Increases operational token cost and execution latency per governance change (one full-authority Bayes call, followed by one bandit call).
- **Cold-Start Conservatism:** In early stages, `escalate-diff-response` will escalate frequently until sufficient contrastive episodes accumulate to cross autonomy thresholds.

## 7. Architectural Invariants

1. `classify-diff-type` MUST always execute under `DecisionAuthority.FULL` using Bayesian multi-criteria evaluation; it must never be converted to a low-authority bandit.
2. `escalate-diff-response` MUST execute under `DecisionAuthority.LOW`, taking `classify-diff-type` outputs strictly via ADR-006 `audit_evidence` without featurizing the policy or corrupting learner isolation.
3. When `classify-diff-type` produces a tie-break disposition (`DecisionStatus.NEEDS_USER_TIE_BREAK` via `minimum_margin <= 0.05`), execution MUST immediately halt and escalate to human review without invoking `escalate-diff-response`.
4. Artifact lifecycle and lineage status mutations (`new_superseding_adr`, `pending_supersession_note`, `supersession_update`) MUST NEVER be applied autonomously; their disposition is permanently locked to require human authorization (`escalate_to_human`).
5. Autonomous governance changes (`apply_automatically` or `apply_with_notification`) MUST NEVER execute silently; every change MUST emit an immutable audit event (`Episode` record).
6. All governance changes applied to the repository MUST be verified via ADR-005 (`compare_decision_results`), ensuring the updated baseline achieves `progression` or neutral tolerance (`flat`) before finalizing the change.
7. ADR-007 scope terminates upon baseline validation; downstream execution changes remain strictly the responsibility of Stage 17 (Adaptation).
8. The pipeline MUST strictly respect ADR-002 Invariant #2: zero new Cosmos DB containers, zero new `LearningStore` record types.

## 8. References

- [`decision.py`](../../src/agent_learning/decision.py) — `TaskPolicy.decide()`, `DecisionFrame.minimum_margin`, `DecisionStatus.NEEDS_USER_TIE_BREAK`, `DecisionResult`
- [`comparison.py`](../../src/agent_learning/comparison.py) — `compare_decision_results()`, `compare_decision_sequence()` (ADR-005)
- Related: [ADR-001](./ADR-001-decision-authority-model.md) — Two-route decision authority architecture
- Related: [ADR-002](./ADR-002-storage-backend-strategy.md) — Five-record-type storage boundary
- Related: [ADR-003](./ADR-003-evidence-gated-autonomy-thresholds.md) — Autonomy complexity tiers and Wilson score gates
- Related: [ADR-005](./ADR-005-decision-progress-comparison.md) — Progress comparison and regression healing
- Related: [ADR-006](./ADR-006-opt-in-lightweight-evidence-capture-for-low-authority.md) — Opt-in lightweight evidence capture and transport boundary
- Project Reference: [`Intent-to-Outcome-Chain-and-TaskPolicy-Coverage.md`](../../../Obsidian%20Brain/wiki/Projects/SocialEngage/09%20AI%20Governance%20&%20Reasoning/Intent-to-Outcome-Chain-and-TaskPolicy-Coverage.md) — 18-stage governance ontology

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-23 | Proposed | Initial formulation of Stage 16 Governance Change paired pipeline, grounded in HYP-AL-006 and HYP-AL-007, integrating ADR-005 progress comparison and ADR-006 evidence transport. |
| 2026-10-23 | Refined (Code-Grounded Review) | Grouped 7-action taxonomy into 3 operational tiers (§4.2); grounded tie-break in SDK's native `DecisionFrame.minimum_margin` (§4.2, §7 Invariant #3); permanently froze all 3 lifecycle lineage actions from autonomy (§4.3, §7 Invariant #4); mandated immutable audit event emission for `apply_automatically` (§4.3, §7 Invariant #5); formalized Stage 17 termination boundary (§4.5, §7 Invariant #7); and added Classification Safety Test Suite (§4.6). |
| 2026-10-23 | Accepted | Evaluated through `approve-adr` TaskPolicy; adjudicated with explicit human approval by Menno Drescher (Episode `9662b831-3a88-4fb9-803b-ed8adde534bf`). Seventh accepted ADR in repository governance lineage. |
| 2026-10-27 | Extension proposed (ADR-037) | ADR-037 (Proposed) adds a design-time input to Stage 16: baseline findings from Stage 7-8, marked `evidence_basis: design_time`, classified and routed by this same pair and sent Stage 16 → Stage 6 without a Stage 17 Adaptation Plan. Section 4.5 is unchanged for the execution route. This ADR's status and text are unchanged until ADR-037 is accepted. |
