"""Extensions to Microsoft's agent-learning, kept apart from it.

Fork rule: modules that came from microsoft/agent-learning are never edited in place, so merging ``upstream/main`` never
clashes with code we wrote. When behaviour has to differ, the Microsoft module is duplicated here and amended in the copy.
``tests/test_upstream_untouched.py`` enforces the rule against the pinned upstream commit.

Our commands and our amended behaviour are reached through ``agent-learn-ext`` (or ``python -m agent_learning_ext``).
Microsoft's ``agent-learn`` stays exactly as Microsoft ships it.

This package is also our public root. ``agent_learning`` exports what Microsoft ships. Everything we added or amended
(governance, the Thompson policy and learner, the PMBOK helpers, the amended decision, autonomy, capture, audit, runner and
learner) is exported here, by name, and loaded on first use so that importing this package never creates an import cycle.
"""

from __future__ import annotations

import importlib
from typing import Any

_EXPORTS: dict[str, str] = {
    "APPLY_AUTOMATICALLY": "agent_learning.governance",
    "APPLY_WITH_NOTIFICATION": "agent_learning.governance",
    "APPROVAL_ACTIONS": "agent_learning.pmbok",
    "ActionDelta": "agent_learning.comparison",
    "AuditReport": "agent_learning_ext.audit",
    "AuditStatus": "agent_learning_ext.audit",
    "AutonomyAssessment": "agent_learning_ext.autonomy",
    "AutonomyConfig": "agent_learning_ext.config",
    "BASELINE_SUBSTANTIATING": "agent_learning.tailoring",
    "Blocker": "agent_learning.pmbok",
    "CAPTURE_DECISION_EVIDENCE_KEY": "agent_learning_ext.decision",
    "CaptureContext": "agent_learning_ext.capture",
    "CatalogEntry": "agent_learning.methodology_catalog",
    "ClassificationType": "agent_learning.comparison",
    "ComplexityAssessment": "agent_learning_ext.autonomy",
    "ComplexityProfile": "agent_learning_ext.autonomy",
    "CosmosStore": "agent_learning_ext.storage.cosmos",
    "CriterionAssessment": "agent_learning_ext.decision",
    "CyclicDependencyError": "agent_learning.pmbok",
    "DAMPING_DEFAULT": "agent_learning.warm_start",
    "DAMPING_DEFAULT_META_PRIOR": "agent_learning.warm_start",
    "DIFF_ACTIONS": "agent_learning.governance",
    "DIFF_TIERS": "agent_learning.governance",
    "DISPOSITIONS": "agent_learning.pmbok",
    "DRAFT_ORDER": "agent_learning.pmbok",
    "DecisionAuthority": "agent_learning_ext.decision",
    "DecisionCriterion": "agent_learning_ext.decision",
    "DecisionFrame": "agent_learning_ext.decision",
    "DecisionOption": "agent_learning_ext.decision",
    "DecisionResolver": "agent_learning_ext.decision",
    "DecisionResult": "agent_learning_ext.decision",
    "DecisionStatus": "agent_learning_ext.decision",
    "DiffActionTier": "agent_learning.governance",
    "ESCALATE_TO_HUMAN": "agent_learning.governance",
    "ESCALATION_ACTIONS": "agent_learning.governance",
    "EpisodeCapture": "agent_learning_ext.capture",
    "EvidencePoint": "agent_learning_ext.decision",
    "ExampleClass": "agent_learning.methodology_catalog",
    "FEEDBACK_STATUSES": "agent_learning.pmbok",
    "FamilyMember": "agent_learning.meta_prior",
    "FitResult": "agent_learning_ext.learners.pairwise",
    "Flag": "agent_learning.tailoring",
    "FormalizationCheck": "agent_learning.pmbok",
    "Freshness": "agent_learning.pmbok",
    "GATE_CRITERIA": "agent_learning.pmbok",
    "GOVERNANCE_CRITERIA_WEIGHTS": "agent_learning.governance",
    "GovernancePipelineResult": "agent_learning.governance",
    "HomeResolution": "agent_learning.tailoring",
    "INTEGRATION_ELEMENTS": "agent_learning.tailoring",
    "InformationNeed": "agent_learning_ext.decision",
    "LearningRunner": "agent_learning_ext.training",
    "LedgerEntry": "agent_learning.methodology_ledger",
    "LessonsLearnedEntry": "agent_learning.lessons_learned",
    "LintFlag": "agent_learning.pmbok",
    "LintResult": "agent_learning.pmbok",
    "MetaPrior": "agent_learning.meta_prior",
    "NextStep": "agent_learning.pmbok",
    "NextStepDecision": "agent_learning.pmbok",
    "OptionAssessment": "agent_learning_ext.decision",
    "PERMANENTLY_FROZEN_DIFF_TYPES": "agent_learning.governance",
    "PLACEHOLDER_TOKENS": "agent_learning.pmbok",
    "PLAN_DAG": "agent_learning.pmbok",
    "PLAN_IDS": "agent_learning.tailoring",
    "PLAN_NAMES": "agent_learning.tailoring",
    "PLAN_STANDARDS": "agent_learning.pmbok",
    "PROVISIONAL_TOKENS": "agent_learning.pmbok",
    "PairwiseComparison": "agent_learning.comparison",
    "PairwiseLearner": "agent_learning_ext.learners.pairwise",
    "ParsedPlan": "agent_learning.pmbok",
    "PlanApprovalRecord": "agent_learning.pmbok",
    "PlanRoute": "agent_learning.tailoring",
    "PlanStandard": "agent_learning.pmbok",
    "PlanState": "agent_learning.pmbok",
    "PreferencePair": "agent_learning_ext.learners.pairwise",
    "ReinforceLearner": "agent_learning_ext.learners.reinforce",
    "Reliability": "agent_learning.review_triage",
    "Route": "agent_learning.tailoring",
    "SequenceComparisonResult": "agent_learning.comparison",
    "TaskPolicy": "agent_learning_ext.decision",
    "ThompsonLearner": "agent_learning.learners.thompson",
    "ThompsonPolicy": "agent_learning.policy.thompson",
    "TieBreakDisposition": "agent_learning_ext.decision",
    "TrainingRunner": "agent_learning_ext.training",
    "TriageRecord": "agent_learning.review_triage",
    "UCBLearner": "agent_learning_ext.learners.ucb",
    "UCBPolicy": "agent_learning_ext.policy.ucb",
    "VALID_DONOR_KINDS": "agent_learning.warm_start",
    "VOLATILE_KEYS": "agent_learning.pmbok",
    "add_rewards": "agent_learning_ext.policy.action_statistics",
    "approval_record": "agent_learning.pmbok",
    "assess_autonomy": "agent_learning_ext.autonomy",
    "assess_complexity": "agent_learning_ext.autonomy",
    "audit_run": "agent_learning_ext.audit",
    "bt_gradient": "agent_learning_ext.learners.pairwise",
    "bt_loss": "agent_learning_ext.learners.pairwise",
    "build_approval_metadata": "agent_learning.pmbok",
    "build_pair_matrix": "agent_learning_ext.learners.pairwise",
    "capture_decision_evidence_enabled": "agent_learning_ext.decision",
    "check_content": "agent_learning.pmbok",
    "check_formalization": "agent_learning.pmbok",
    "check_plan_freshness": "agent_learning.pmbok",
    "compare_decision_results": "agent_learning.comparison",
    "compare_decision_sequence": "agent_learning.comparison",
    "compile_meta_prior": "agent_learning.meta_prior",
    "compute_canonical_plan_hash": "agent_learning.pmbok",
    "compute_flags": "agent_learning.tailoring",
    "count_words": "agent_learning.pmbok",
    "current_entries": "agent_learning.methodology_ledger",
    "derive_class": "agent_learning.methodology_catalog",
    "derive_plan_state": "agent_learning.pmbok",
    "effective_upstreams": "agent_learning.pmbok",
    "evaluate_governance_diff": "agent_learning.governance",
    "entropy": "agent_learning_ext.routing",
    "entropy_bits": "agent_learning_ext.routing",
    "filter_crystallized_lessons": "agent_learning.lessons_learned",
    "find_triage_lines": "agent_learning.review_triage",
    "fit_logits": "agent_learning_ext.learners.pairwise",
    "gate_constraint_results": "agent_learning.pmbok",
    "get_capture": "agent_learning_ext.capture",
    "get_default_store": "agent_learning_ext.storage.cosmos",
    "integrity_flags": "agent_learning.pmbok",
    "is_raw_hash": "agent_learning.pmbok",
    "latest_approvals": "agent_learning.pmbok",
    "lint_plan": "agent_learning.pmbok",
    "load_lessons_learned_register": "agent_learning.lessons_learned",
    "margin": "agent_learning_ext.routing",
    "next_step": "agent_learning.pmbok",
    "omission_flags": "agent_learning.pmbok",
    "parse_catalog": "agent_learning.methodology_catalog",
    "parse_frontmatter": "agent_learning.pmbok",
    "parse_ledger": "agent_learning.methodology_ledger",
    "parse_lessons_learned_markdown": "agent_learning.lessons_learned",
    "parse_triage_line": "agent_learning.review_triage",
    "pairs_from_episodes": "agent_learning_ext.learners.pairwise",
    "plan_hash": "agent_learning.pmbok",
    "provenance": "agent_learning.warm_start",
    "raw_change_hash": "agent_learning.pmbok",
    "reconstruct_record": "agent_learning.review_triage",
    "reliability": "agent_learning.review_triage",
    "resolve_home": "agent_learning.tailoring",
    "reward_to_r": "agent_learning_ext.policy.action_statistics",
    "seed_values": "agent_learning.meta_prior",
    "to_episode_metadata": "agent_learning.tailoring",
    "topological_order": "agent_learning.pmbok",
    "ucb_scores": "agent_learning_ext.policy.ucb",
    "validate_catalog": "agent_learning.methodology_catalog",
    "validate_dependencies": "agent_learning.pmbok",
    "validate_metadata": "agent_learning.pmbok",
    "validate_route_set": "agent_learning.tailoring",
    "warm_start_logits": "agent_learning.warm_start",
    "wilson_lower_bound": "agent_learning_ext.autonomy"
}

__all__ = sorted(_EXPORTS)  # noqa: PLE0605


def __getattr__(name: str) -> Any:
    module = _EXPORTS.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(importlib.import_module(module), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted([*globals(), *_EXPORTS])
