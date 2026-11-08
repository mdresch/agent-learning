# Cross-System Integration Study: Scout, ADPA, and SIDPA

> **Library:** Spark & Ideation Research Library (`docs/research/ideation/`)  
> **Source Investigation:** Phase 1 Cross-System Architecture & Production Adoption  
> **Target Systems:** Microsoft Scout, ADPA (Automated Design & Process Auditor), RPAS-BA-Workbench / SIDPA

---

## 1. Executive Summary

This study documents empirical research into real-world systems outside `agent-learning` itself to verify:
1. Production adoption of the core decision-authority engine in Microsoft's flagship agent **Scout**.
2. Opportunity areas for bandit-based dynamic quality gates in **ADPA**.
3. Opportunities for calibrated value metrics (Enterprise Value Index / Confidence Factor) in **SIDPA**.

---

## 2. Microsoft Scout Production Adoption

### 2.1 Code-Level Archaeological Verification
Rather than relying on documentation claims, production adoption was verified directly against repository commit history and source code:
- **Documentation Artifacts:** [`docs/scout-agent-learn-skill.md`](../../scout-agent-learn-skill.md) and [`docs/scout-automation-agent-learning.md`](../../scout-automation-agent-learning.md) describe the exact operational pattern Scout uses to consult and record against a `TaskPolicy` for delegated choices among executable alternatives.
- **Commit History & Authorship:** Verified via `git log --follow`: authored by **`ctava-msft`** across 10 iterative commits (2026-08-07 to 2026-08-10). `ctava-msft` is Chris Tava (Microsoft, author of [`docs/research/main.tex`](../main.tex)).
- **Runtime Interfaces:** Fields `policy_scope`, `delegated_decision`, and `decision_authority` are implemented in `src/agent_learning/decision.py`, `cli.py`, and `audit.py`.
- **Test Fixtures:** Real fixture data committed under `data/functional-tests/patient-care-cli/policies/triage-nurse/*.json`.

### 2.2 Architectural Significance
Scout uses `low` authority (`SoftmaxPolicy` + REINFORCE) for stable, bounded choices (e.g. `choose-azure-pubsub-message-processor`) and `full` authority (`DecisionResolver` frames) for complex per-instance request delegations (e.g. deployment-region selection). This proves that the dual-authority model is a live production architecture at Microsoft, not a speculative concept.

---

## 3. ADPA (Automated Design & Process Auditor) Integration Opportunities

### 3.1 Quality-Gate Bandit Calibration (`HYP-AL-012`)
ADPA currently applies static hand-set thresholds across three layers:
1. *Template Regression:* Flat 15-percentage-point quality drop trigger (`qualityRegressionDetector.ts`).
2. *Template Health:* Static 70-point success cutoff and 0.4/0.4/0.1/0.1 weighted average (`templateHealthService.ts`).
3. *Compliance Rules:* Hand-set pass/warning/fail thresholds (`modules/compliance/types.ts`).

**Research Finding:** Real per-template time-series data exists in `quality_audits.overall_score`, making layers 1–2 testable with a confidence-interval bandit (Wilson bound / UCB). Layer 3 remains unconfirmed due to empty compliance tables in earlier audits.

### 3.2 Governance Council Human-Override Learning (`HYP-AL-013`)
ADPA's `councilRouter.ts` records AI tribunal verdicts alongside mandatory human auditor override decisions in `governance_audit_ledger`.
- **Opportunity:** A `low`-authority `TaskPolicy` can learn which categories of DRACO tribunal verdicts humans reliably agree with vs override.

### 3.3 Active Pairwise Ranking (`HYP-AL-015`)
`PairwiseComparisonMatrix.tsx` generates all $n(n-1)/2$ pairs exhaustively (190 comparisons for 20 projects) with no adaptive selection.
- **Opportunity:** Dueling-bandit active ranking (Methodology #23, Bradley-Terry model) can reach equivalent ranking confidence with dramatically fewer human queries.

---

## 4. RPAS-BA-Workbench & SIDPA Solution Evaluation Opportunities

### 4.1 Enterprise Value Index (EVI) Dynamic Thresholds (`HYP-AL-014`)
`SolutionEvaluationModels.cs` compiles five static composite floors (`EviCompositeFloor=85`, `PowerScoreFloor=80`, `CostScoreFloor=80`, `LatencyScoreFloor=75`, `ReliabilityScoreFloor=85`).
- **Research Finding:** `CalculateEnterpriseValueIndex()` is live executing code, but relies on an in-memory instance field `_currentEvi` with no persisted time-series. Any learning mechanism requires a persistent telemetry table before calibration is feasible.

### 4.2 Calibrated Confidence Factor & Accuracy Factor (`HYP-AL-016`)
The SIDPA prospectus proposes a multiplicative Intelligence-Capital metric $IPC = RC \times AF \times AV \times CF$.
- **Research Finding:** Existing code implements an additive hardware-efficiency composite rather than multiplicative IPC. A `low`-authority `TaskPolicy` can calibrate CF and AF once true IPC logging is established.

---

## 5. Architectural Recommendations for Future Phases

1. **Prioritize Packaged Contextual Bandits:** Both Scout and SocialEngage workarounds highlight that developers resort to manual `full`-authority frames when contextual bandits are unpackaged.
2. **Standardize Evidence Ingestion:** Automated critique-to-evidence (Option B / Epic 14) directly addresses the gap where human review comments cannot currently be ingested as training signals.
