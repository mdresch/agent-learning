"""Metric scores are turned into one bounded reward, with a latency penalty.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #5 Pluggable reward shaping
ADR: none
HYPOTHESIS: none
NOT EVIDENCE: this run does not validate or invalidate the methodology. The metric scores and latencies are invented.
"""

from __future__ import annotations

from agent_learning.config import ShapingConfig
from agent_learning.rewards import shape_episode_reward
from agent_learning.types import Episode, MetricName, MetricResult


def metrics(score: float) -> list[MetricResult]:
    return [
        MetricResult(metric=metric, score=score, normalized=score, status="completed")
        for metric in (MetricName.INTENT_RESOLUTION, MetricName.TASK_ADHERENCE, MetricName.TASK_COMPLETION)
    ]


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate reward shaping.")
    config = ShapingConfig()
    cases = {
        "good and fast": (0.9, 1_000),
        "good but slow": (0.9, 60_000),
        "poor and fast": (0.2, 1_000),
    }
    shaped = {}
    for label, (score, latency_ms) in cases.items():
        episode = Episode(id=label, agent_id="demo-agent", request_latency_ms=latency_ms)
        shaped[label] = shape_episode_reward(episode, metrics(score), config)
        print(f"{label:14s} reward={shaped[label].value:+.3f} penalties={shaped[label].penalties}")

    assert all(-1.0 <= r.value <= 1.0 for r in shaped.values())
    assert shaped["good and fast"].value > shaped["good but slow"].value > shaped["poor and fast"].value


if __name__ == "__main__":
    main()
