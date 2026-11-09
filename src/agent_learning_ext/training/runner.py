# ext-source: src/agent_learning/training/runner.py sha256:b43b160f980cb2d1b08c76b7ec0493d1827b7d56100e5c41fa36442e9c03c72c
# ruff: noqa  (kept faithful to Microsoft's code and style so upstream changes merge in cleanly)
# Copy of Microsoft's module for agent_learning_ext (fork rule: Microsoft's file is never edited).
# EXT: imports the amended ReinforceLearner, so the exact-type replay check in _record_replay_configuration still matches.
# When the upstream pin moves and the source file changes, merge that change here and update the hash above.
"""End-to-end native learning loop.

The :class:`LearningRunner` ties together the four moving parts:

1. ``MetricEvaluator``s evaluate each episode with the three scorers.
2. ``RewardShaper`` collapses metrics into a scalar reward.
3. ``RewardWriter`` persists per-metric and aggregate rewards.
4. ``Learner`` consumes recent episodes + their aggregate rewards
   and applies one update to the current ``Policy``.

The runner is intentionally synchronous and stateless: callers
control the cadence (cron, manual, event-driven). Each invocation
of :meth:`run_offline_batch` is one training step.
"""

from __future__ import annotations

import logging
import platform
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

import numpy as np

from agent_learning._version import __version__
from agent_learning.config import LearnerConfig, ScoreConfig, ScoreRuntimeConfig, ShapingConfig
from agent_learning.learners.base import Learner, LearnerResult
from agent_learning_ext.learners.reinforce import ReinforceLearner
from agent_learning.metrics.base import MetricEvaluator
from agent_learning.metrics.registry import default_metrics, evaluate_all
from agent_learning.policy.base import Policy
from agent_learning.policy.softmax_bandit import SoftmaxPolicy
from agent_learning.rewards.shaping import RewardShaper, shape_episode_reward
from agent_learning.rewards.writer import RewardWriter
from agent_learning.storage.base import LearningStore
from agent_learning_ext.storage.cosmos import get_default_store
from agent_learning.types import Episode, MetricResult, Reward, TrainingRun, TrainingStatus

logger = logging.getLogger(__name__)


class LearningRunner:
    """Orchestrates the evaluate → shape → learn pipeline."""

    def __init__(
        self,
        *,
        store: Optional[LearningStore] = None,
        policy: Optional[Policy] = None,
        metrics: Optional[Iterable[MetricEvaluator]] = None,
        shaper: Optional[RewardShaper] = None,
        writer: Optional[RewardWriter] = None,
        learner: Optional[Learner] = None,
        score_config: Optional[ScoreConfig] = None,
        score_runtime_config: Optional[ScoreRuntimeConfig] = None,
        learner_config: Optional[LearnerConfig] = None,
        shaping_config: Optional[ShapingConfig] = None,
    ) -> None:
        self._store = store or get_default_store()
        self._policy = policy
        self._metrics = (
            list(metrics)
            if metrics is not None
            else default_metrics(score_config, score_runtime_config)
        )
        self._shaper = shaper or RewardShaper(shaping_config)
        self._writer = writer or RewardWriter(self._store)
        self._learner = learner or ReinforceLearner(learner_config)

    # ------------------------------------------------------------------
    # Per-episode pipeline
    # ------------------------------------------------------------------

    def evaluate_episode(self, episode: Episode) -> List[MetricResult]:
        """Run all metrics over an episode without writing anything."""
        return evaluate_all(episode, self._metrics)

    def score_and_record(self, episode: Episode) -> List[Reward]:
        """Evaluate, shape, and persist rewards for one episode."""
        results = self.evaluate_episode(episode)
        shaped = shape_episode_reward(episode, results, self._shaper.config)
        return self._writer.write(episode, results, shaped)

    # ------------------------------------------------------------------
    # Batched offline learning
    # ------------------------------------------------------------------

    def run_offline_batch(
        self,
        agent_id: str,
        *,
        task_id: str = "default",
        episode_limit: int = 200,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        score_missing: bool = True,
    ) -> TrainingRun:
        """Score (if missing) and update the policy over recent episodes."""
        if self._policy is None:
            raise RuntimeError("A Policy must be supplied before running a batch update.")

        run = TrainingRun(
            agent_id=agent_id,
            task_id=task_id,
            policy_id=self._policy.snapshot().id,
            algorithm=type(self._learner).__name__,
            status=TrainingStatus.RUNNING,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self._store.store_run(run)

        try:
            episodes = self._store.query_episodes(
                agent_id,
                limit=episode_limit,
                start_date=start_date,
                end_date=end_date,
                task_id=task_id,
                full_only=True,
            )
            rewards = self._collect_rewards(agent_id, episodes, score_missing=score_missing)

            self._record_replay_configuration(run)
            result = self._learner.update(self._policy, episodes, rewards)
            policy_snapshot = self._policy.snapshot()
            self._store.store_policy(policy_snapshot)

            run.status = TrainingStatus.SUCCEEDED
            run.completed_at = datetime.now(timezone.utc).isoformat()
            run.episode_ids = [ep.id for ep in episodes]
            run.output_policy_id = policy_snapshot.id
            run.consumed_inputs = (
                list(result.consumed_inputs) if result.consumed_inputs is not None else None
            )
            run.metrics = _summarise_result(result)
            run.metadata.update(
                {
                    "policy_version": policy_snapshot.version,
                    "task_id": task_id,
                    "score_missing": score_missing,
                }
            )
            self._store.store_run(run)
            return run
        except Exception as exc:  # pragma: no cover - defensive path
            run.status = TrainingStatus.FAILED
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc).isoformat()
            self._store.store_run(run)
            raise

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _record_replay_configuration(self, run: TrainingRun) -> None:
        # Subclasses may change update semantics even when they inherit config.
        if type(self._learner) is not ReinforceLearner or type(self._policy) is not SoftmaxPolicy:
            return
        config = self._learner.config
        run.hyperparameters = {
            "learner": {
                "learning_rate": config.learning_rate,
                "baseline_decay": config.baseline_decay,
                "entropy_bonus": config.entropy_bonus,
                "importance_clip": config.importance_clip,
            },
            "policy": {"max_logit_abs": self._policy.max_logit_abs},
        }
        run.metadata.update(
            {
                "lineage_version": 1,
                "replay_implementation": "reinforce_softmax_v1",
                "runtime_versions": {
                    "agent_learning": __version__,
                    "python": platform.python_version(),
                    "numpy": np.__version__,
                },
            }
        )

    def has_usable_reward(self, episode: Episode) -> bool:
        """Return whether an episode has an aggregate backed by valid metrics."""
        rewards = self._store.get_rewards_for_episode(episode.id, episode.agent_id)
        if not any(reward.source.value == "aggregate" for reward in rewards):
            return False
        metrics = self._store.get_metric_results(episode.id, episode.agent_id)
        if not metrics:
            return True
        return any(
            result.status == "completed" and result.normalized is not None
            for result in metrics
        )

    def _collect_rewards(
        self,
        agent_id: str,
        episodes: Iterable[Episode],
        *,
        score_missing: bool,
    ) -> List[Reward]:
        rewards: List[Reward] = []
        for episode in episodes:
            existing = self._store.get_rewards_for_episode(episode.id, agent_id)
            if self.has_usable_reward(episode):
                rewards.extend(existing)
                continue
            if not score_missing:
                continue
            scored = self.score_and_record(episode)
            rewards.extend(scored)
        return rewards


def _summarise_result(result: LearnerResult) -> Dict[str, object]:
    """Project a :class:`LearnerResult` into a Cosmos-friendly dict."""
    return {
        "episodes_used": result.episodes_used,
        "mean_reward": result.mean_reward,
        "baseline_before": result.baseline_before,
        "baseline_after": result.baseline_after,
        "logit_deltas": result.logit_deltas,
        "extra": result.extra,
    }


# Alias per ADR-018 / FDD-018
TrainingRunner = LearningRunner

__all__ = ["LearningRunner", "TrainingRunner"]
