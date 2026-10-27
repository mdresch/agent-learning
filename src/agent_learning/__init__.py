"""Evidence-driven reasoned and learned decision SDK for AI agents.

Replaces the agent-lightning LLM fine-tuning loop with a fully
native, in-process learner. The SDK is organised into five layers:

- ``agent_learning.types``    - durable record types (``Episode``,
  ``Reward``, ``PolicySnapshot``, ...).
- ``agent_learning.storage``  - pluggable persistence (Cosmos DB,
  local file system, and in-memory).
- ``agent_learning.metrics``  - on-device stdlib metrics by default,
    with optional Azure AI evaluators for Intent Resolution, Task
    Adherence, and Task Completion.
- ``agent_learning.rewards``  - reward shaping + persistence.
- ``agent_learning.decision`` - unified reasoned and learned task decisions.
- ``agent_learning.policy``   - discrete softmax bandit policy.
- ``agent_learning.learners`` - REINFORCE-with-baseline learner.
- ``agent_learning.training`` - end-to-end :class:`LearningRunner`.

Quick start::

    from agent_learning import (
        Action,
        EpisodeCapture,
        LearningRunner,
        SoftmaxPolicy,
    )

    actions = [Action(id="prompt_A"), Action(id="prompt_B")]
    policy = SoftmaxPolicy.from_actions(actions, agent_id="dq", task_id="sales-summary")

    # Capture
    capture = EpisodeCapture()
    decision = policy.choose()
    ctx = capture.start(
        "Tell me my Q3 sales summary",
        task_id="sales-summary",
        intent_summary="Summarize Q3 sales",
        action_type="chat",
        action_name=decision.action.id,
        expected_outcome="An accurate Q3 sales summary",
        policy_id=policy.snapshot().id,
        policy_version=policy.snapshot().version,
        action_id=decision.action.id,
        action_logprob=decision.logprob,
    )
    # ... agent runs, records tool calls, produces output ...
    episode = capture.end(
        ctx,
        assistant_output="...",
        execution_status="completed",
        result_summary="Returned the sales summary",
    )

    # Train
    runner = LearningRunner(policy=policy)
    run = runner.run_offline_batch("dq", task_id="sales-summary", episode_limit=200)
"""

from ._version import __version__
from .audit import AuditReport, AuditStatus, audit_run
from .autonomy import (
    AutonomyAssessment,
    ComplexityAssessment,
    ComplexityProfile,
    assess_autonomy,
    assess_complexity,
    wilson_lower_bound,
)
from .capture import CaptureContext, EpisodeCapture, get_capture
from .lessons_learned import (
    LessonsLearnedEntry,
    filter_crystallized_lessons,
    load_lessons_learned_register,
    parse_lessons_learned_markdown,
)
from .methodology_catalog import (
    CatalogEntry,
    ExampleClass,
    derive_class,
    parse_catalog,
    validate_catalog,
)
from .methodology_ledger import (
    LedgerEntry,
    current_entries,
    parse_ledger,
)
from .review_triage import (
    Reliability,
    TriageRecord,
    find_triage_lines,
    parse_triage_line,
    reconstruct_record,
    reliability,
)
from .pmbok import (
    PLAN_STANDARDS,
    LintFlag,
    LintResult,
    NextStep,
    NextStepDecision,
    ParsedPlan,
    PlanStandard,
    check_content,
    count_words,
    lint_plan,
    next_step,
    omission_flags,
    parse_frontmatter,
    validate_metadata,
)
from .tailoring import (
    BASELINE_SUBSTANTIATING,
    INTEGRATION_ELEMENTS,
    PLAN_IDS,
    PLAN_NAMES,
    Flag,
    HomeResolution,
    PlanRoute,
    Route,
    compute_flags,
    resolve_home,
    to_episode_metadata,
    validate_route_set,
)
from .governance import (
    APPLY_AUTOMATICALLY,
    APPLY_WITH_NOTIFICATION,
    DIFF_ACTIONS,
    DIFF_TIERS,
    DiffActionTier,
    ESCALATE_TO_HUMAN,
    ESCALATION_ACTIONS,
    GOVERNANCE_CRITERIA_WEIGHTS,
    GovernancePipelineResult,
    PERMANENTLY_FROZEN_DIFF_TYPES,
    evaluate_governance_diff,
)
from .comparison import (
    DEFAULT_EPSILON,
    ActionDelta,
    ClassificationType,
    PairwiseComparison,
    SequenceComparisonResult,
    compare_decision_results,
    compare_decision_sequence,
)
from .classifiers import (
    AdherenceScorer,
    Classifier,
    ClassifierResult,
    CompletionScorer,
    IntentScorer,
    RouterClassifier,
)
from .config import (
    AutonomyConfig,
    AutonomyTier,
    CaptureConfig,
    CosmosConfig,
    LearnerConfig,
    ScoreConfig,
    ShapingConfig,
)
from .decision import (
    CAPTURE_DECISION_EVIDENCE_KEY,
    CriterionAssessment,
    DecisionAuthority,
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionResolver,
    DecisionResult,
    DecisionStatus,
    EvidencePoint,
    InformationNeed,
    OptionAssessment,
    TaskPolicy,
    TieBreakDisposition,
    capture_decision_evidence_enabled,
)
from .learners import Learner, LearnerResult, ReinforceLearner
from .metrics import (
    IntentResolutionMetric,
    MetricEvaluator,
    MetricRequest,
    TaskAdherenceMetric,
    TaskCompletionMetric,
    default_metrics,
    evaluate_all,
)
from .policy import ContextualSoftmaxPolicy, Policy, SoftmaxPolicy
from .rewards import RewardShaper, RewardWriter, shape_episode_reward
from .storage import (
    CosmosStore,
    InMemoryStore,
    LearningStore,
    LocalFileStore,
    get_default_store,
)
from .spark import SparkEpisodeScorer, score_episode_dataframe
from .training import LearningRunner
from .types import (
    Action,
    AgentSummary,
    AgentTaskSummary,
    ConsumedInput,
    Episode,
    MetricName,
    MetricResult,
    PolicySnapshot,
    Reward,
    RewardSource,
    ToolCall,
    TrainingRun,
    TrainingStatus,
)

__all__ = [
    "Action",
    "APPLY_AUTOMATICALLY",
    "APPLY_WITH_NOTIFICATION",
    "DIFF_ACTIONS",
    "DIFF_TIERS",
    "DiffActionTier",
    "ESCALATE_TO_HUMAN",
    "ESCALATION_ACTIONS",
    "GOVERNANCE_CRITERIA_WEIGHTS",
    "GovernancePipelineResult",
    "PERMANENTLY_FROZEN_DIFF_TYPES",
    "evaluate_governance_diff",
    "LessonsLearnedEntry",
    "filter_crystallized_lessons",
    "load_lessons_learned_register",
    "derive_class",
    "parse_lessons_learned_markdown",
    "parse_catalog",
    "BASELINE_SUBSTANTIATING",
    "INTEGRATION_ELEMENTS",
    "PLAN_IDS",
    "PLAN_NAMES",
    "Flag",
    "HomeResolution",
    "PlanRoute",
    "Route",
    "compute_flags",
    "resolve_home",
    "to_episode_metadata",
    "validate_route_set",

    "ActionDelta",
    "ClassificationType",
    "PairwiseComparison",
    "SequenceComparisonResult",
    "compare_decision_results",
    "compare_decision_sequence",
    "AdherenceScorer",
    "AgentSummary",
    "AgentTaskSummary",
    "AuditReport",
    "AuditStatus",
    "AutonomyAssessment",
    "AutonomyConfig",
    "AutonomyTier",
    "CaptureConfig",
    "CatalogEntry",
    "CaptureContext",
    "Classifier",
    "ClassifierResult",
    "CompletionScorer",
    "ComplexityAssessment",
    "ComplexityProfile",
    "ExampleClass",
    "ConsumedInput",
    "ContextualSoftmaxPolicy",
    "CosmosConfig",
    "CosmosStore",
    "CriterionAssessment",
    "DecisionAuthority",
    "DecisionCriterion",
    "DecisionFrame",
    "DecisionOption",
    "DecisionResolver",
    "DecisionResult",
    "DecisionStatus",
    "Episode",
    "EpisodeCapture",
    "EvidencePoint",
    "InMemoryStore",
    "InformationNeed",
    "IntentResolutionMetric",
    "IntentScorer",
    "Learner",
    "LearnerConfig",
    "LearnerResult",
    "LearningRunner",
    "LearningStore",
    "LocalFileStore",
    "MetricEvaluator",
    "MetricName",
    "MetricRequest",
    "MetricResult",
    "OptionAssessment",
    "Policy",
    "PolicySnapshot",
    "ReinforceLearner",
    "Reward",
    "RewardShaper",
    "RewardSource",
    "RewardWriter",
    "RouterClassifier",
    "ScoreConfig",
    "ShapingConfig",
    "SoftmaxPolicy",
    "SparkEpisodeScorer",
    "TaskAdherenceMetric",
    "TaskCompletionMetric",
    "TaskPolicy",
    "TieBreakDisposition",
    "ToolCall",
    "TrainingRun",
    "TrainingStatus",
    "__version__",
    "assess_autonomy",
    "assess_complexity",
    "audit_run",
    "default_metrics",
    "evaluate_all",
    "get_capture",
    "get_default_store",
    "score_episode_dataframe",
    "validate_catalog",
    "CAPTURE_DECISION_EVIDENCE_KEY",
    "capture_decision_evidence_enabled",
    "Reliability",
    "TriageRecord",
    "find_triage_lines",
    "parse_triage_line",
    "reconstruct_record",
    "reliability",
    "LedgerEntry",
    "current_entries",
    "parse_ledger",
    "PLAN_STANDARDS",
    "LintFlag",
    "ParsedPlan",
    "PlanStandard",
    "parse_frontmatter",
    "validate_metadata",
    "LintResult",
    "check_content",
    "count_words",
    "lint_plan",
    "omission_flags",
    "NextStep",
    "NextStepDecision",
    "next_step",
    "shape_episode_reward",
    "wilson_lower_bound",
]
