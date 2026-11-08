"""Thompson sampling policy state and seeded, replayable draws (ADR-015, FDD-015).

The posterior lives in ``PolicySnapshot.metadata`` (no new record type, ADR-002). Nothing here
reads the store or touches a file; the caller persists the snapshot.
"""

from __future__ import annotations

import copy
import hashlib
import hmac
import math
import random
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..types import Action, PolicySnapshot
from .base import Decision, Policy


@dataclass
class ThompsonDecision(Decision):
    """A Decision with no selection probability: probability matching has none (ADR-015)."""

    logprob: float | None


PRIOR_ALPHA = 1.0
PRIOR_BETA = 1.0
N_MAX = 5000.0  # ceiling on alpha + beta per action (BRU-015-05)
SELECTION_BASIS = "thompson_sampling"  # Episode.metadata["selection_basis"] for a Thompson decision


def seed_for(policy_id: str, request_id: str, timestamp: str) -> int:
    """Return the 64-bit PRNG seed for one request against one policy.

    ``int(HMAC-SHA256(key=policy_id, msg=request_id + "|" + timestamp).hexdigest()[:16], 16)``.
    The fixed ``"|"`` separator keeps two different pairs from joining to one message.
    """
    for name, value in (("policy_id", policy_id), ("request_id", request_id), ("timestamp", timestamp)):
        if not value:
            raise ValueError(f"{name} must not be empty")
    digest = hmac.new(
        policy_id.encode("utf-8"),
        (request_id + "|" + timestamp).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return int(digest[:16], 16)


def replay(record: Mapping[str, Any], policy_id: str) -> dict[str, float]:
    """Redraw the payoffs of a sampling record and return them.

    Re-derives the seed from the record's ``request_id`` and ``timestamp`` and ``policy_id``,
    checks it equals ``prng_seed``, then redraws ``betavariate(alpha, beta)`` per action in the
    order of ``posterior_parameters["alpha"]``. The record is not changed and no store is read.

    Raises:
        ValueError: if the seed differs from ``prng_seed``, or if the redraw differs from
            ``sampled_payoffs`` (a different Python version, not proof of tampering).
    """
    expected = seed_for(policy_id, record["request_id"], record["timestamp"])
    if str(expected) != str(record["prng_seed"]):
        raise ValueError(
            f"seed mismatch: record prng_seed {record['prng_seed']!r} is not the seed {expected} "
            "derived from policy_id, request_id and timestamp"
        )

    posterior = record["posterior_parameters"]
    rng = random.Random(expected)
    redrawn = {
        action_id: rng.betavariate(posterior["alpha"][action_id], posterior["beta"][action_id])
        for action_id in posterior["alpha"]
    }
    if redrawn != dict(record["sampled_payoffs"]):
        raise ValueError(
            "redrawn payoffs differ from sampled_payoffs: a Python version difference "
            "(random.Random.betavariate is not stable across versions)"
        )
    return redrawn


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _read_parameters(
    raw: object, name: str, action_ids: Sequence[str], prior: float
) -> dict[str, float]:
    """Validate one of ``alpha`` or ``beta`` and return it with every action present."""
    if not isinstance(raw, Mapping):
        raise ValueError(f"posterior_parameters[{name!r}] must be a mapping keyed by action id")  # noqa: TRY004
    unknown = [action_id for action_id in raw if action_id not in action_ids]
    if unknown:
        raise ValueError(f"posterior_parameters[{name!r}] names action {unknown[0]!r} outside the action space")
    out: dict[str, float] = {}
    for action_id in action_ids:
        if action_id not in raw:
            out[action_id] = prior
            continue
        value = raw[action_id]
        if not _is_number(value) or not math.isfinite(value) or value <= 0:
            raise ValueError(
                f"posterior_parameters[{name!r}] for action {action_id!r} must be finite and positive, "
                f"got {value!r}"
            )
        out[action_id] = float(value)
    return out


def _read_consumed(raw: object) -> list[str]:
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ValueError("consumed_episode_ids must be a list of episode id strings")
    seen: set[str] = set()
    for item in raw:
        if item in seen:
            raise ValueError(f"consumed_episode_ids holds {item!r} more than once")
        seen.add(item)
    return list(raw)


class ThompsonPolicy(Policy):
    """Beta-Bernoulli posterior per action, kept in the policy snapshot (FDD-015 §1 item 3, §2.2).

    ``metadata["posterior_parameters"]`` holds ``{"alpha": {action_id: x}, "beta": {...}}`` and
    ``metadata["consumed_episode_ids"]`` the ids of the episodes already counted (D7). ``logits``
    stays at zero: a posterior has no logits. Drawing is Story 15.3, learning Story 15.4.
    """

    def __init__(self, snapshot: PolicySnapshot) -> None:
        if not snapshot.actions:
            raise ValueError("ThompsonPolicy requires at least one action.")
        action_ids = [action.id for action in snapshot.actions]
        raw = snapshot.metadata.get("posterior_parameters", {})
        if not isinstance(raw, Mapping):
            raise ValueError("posterior_parameters must be a mapping with 'alpha' and 'beta'")  # noqa: TRY004
        unexpected = [key for key in raw if key not in ("alpha", "beta")]
        if unexpected:
            raise ValueError(f"posterior_parameters has unexpected key {unexpected[0]!r}")
        alpha = _read_parameters(raw.get("alpha", {}), "alpha", action_ids, PRIOR_ALPHA)
        beta = _read_parameters(raw.get("beta", {}), "beta", action_ids, PRIOR_BETA)
        consumed = _read_consumed(snapshot.metadata.get("consumed_episode_ids", []))

        # Keep a copy so the caller's snapshot is never changed (I3).
        self._snapshot = PolicySnapshot.from_dict(snapshot.to_dict())
        self._snapshot.metadata = {
            **{k: v for k, v in snapshot.metadata.items() if k not in ("posterior_parameters", "consumed_episode_ids")},
            "posterior_parameters": {"alpha": alpha, "beta": beta},
            "consumed_episode_ids": consumed,
        }
        for action_id in action_ids:
            self._snapshot.logits.setdefault(action_id, 0.0)
        self._last_record: dict[str, Any] | None = None

    @classmethod
    def from_actions(
        cls, actions: Sequence[Action], *, agent_id: str = "default", task_id: str = "default"
    ) -> ThompsonPolicy:
        snapshot = PolicySnapshot(
            agent_id=agent_id,
            task_id=task_id,
            version=0,
            actions=list(actions),
            logits={action.id: 0.0 for action in actions},
        )
        return cls(snapshot)

    @classmethod
    def from_snapshot(cls, snapshot: PolicySnapshot) -> ThompsonPolicy:
        return cls(snapshot)

    def posterior(self) -> dict[str, dict[str, float]]:
        """A copy of the posterior, with every action present."""
        stored = self._snapshot.metadata["posterior_parameters"]
        return {"alpha": dict(stored["alpha"]), "beta": dict(stored["beta"])}

    def consumed_episode_ids(self) -> list[str]:
        """A copy of the ids of the episodes already counted."""
        return list(self._snapshot.metadata["consumed_episode_ids"])

    def update_posterior(
        self,
        alpha: Mapping[str, float],
        beta: Mapping[str, float],
        consumed_episode_ids: Sequence[str],
        *,
        episodes_seen: int,
    ) -> None:
        """Replace the posterior and the consumed ids, as :class:`ThompsonLearner` does.

        The new state is validated as ``from_snapshot`` validates it, before anything is written,
        so a refused update leaves the policy as it was. ``logits`` stays at zero.
        """
        action_ids = [action.id for action in self._snapshot.actions]
        new_alpha = _read_parameters(alpha, "alpha", action_ids, PRIOR_ALPHA)
        new_beta = _read_parameters(beta, "beta", action_ids, PRIOR_BETA)
        consumed = _read_consumed(list(consumed_episode_ids))
        self._snapshot.metadata["posterior_parameters"] = {"alpha": new_alpha, "beta": new_beta}
        self._snapshot.metadata["consumed_episode_ids"] = consumed
        self._snapshot.episodes_seen = int(episodes_seen)
        self._snapshot.updates_applied += 1
        self._snapshot.advance_version()

    def actions(self) -> Sequence[Action]:
        return tuple(self._snapshot.actions)

    def snapshot(self) -> PolicySnapshot:
        return PolicySnapshot.from_dict(self._snapshot.to_dict())

    def choose(
        self,
        state: Any = None,
        *,
        request_id: str | None = None,
        timestamp: str | None = None,
    ) -> Decision:
        """Draw once per action from its Beta posterior and take the highest draw (FDD-015 §3 item 3).

        ``state`` is ignored: the posterior is marginal. A missing ``request_id`` or ``timestamp``
        is supplied (a new UUID, the current UTC time) and recorded. The draws are seeded by
        ``seed_for(snapshot.id, request_id, timestamp)`` in snapshot order; a tie goes to the
        earlier action. The record is available from :meth:`last_sampling_record`.

        ``Decision.logprob`` is ``None``: probability matching has no selection probability.
        ``Decision.probabilities`` is the draw-free posterior mean ``alpha / (alpha + beta)``
        normalised over the actions, for display only. It is **not** the selection probability.
        """
        del state
        if request_id is None:
            request_id = str(uuid.uuid4())
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()
        seed = seed_for(self._snapshot.id, request_id, timestamp)

        posterior = self.posterior()
        rng = random.Random(seed)
        draws = {
            action.id: rng.betavariate(posterior["alpha"][action.id], posterior["beta"][action.id])
            for action in self._snapshot.actions
        }
        best = 0
        for index, action in enumerate(self._snapshot.actions):
            if draws[action.id] > draws[self._snapshot.actions[best].id]:
                best = index

        means = [
            posterior["alpha"][a.id] / (posterior["alpha"][a.id] + posterior["beta"][a.id])
            for a in self._snapshot.actions
        ]
        total = sum(means)
        self._last_record = {
            "request_id": request_id,
            "timestamp": timestamp,
            "prng_seed": str(seed),
            "posterior_parameters": posterior,
            "sampled_payoffs": draws,
        }
        return ThompsonDecision(
            action=self._snapshot.actions[best],
            logprob=None,
            probabilities=[mean / total for mean in means],
        )

    def last_sampling_record(self) -> dict[str, Any] | None:
        """A deep copy of the FDD-015 §2.3 record of the latest ``choose``, or ``None`` before one."""
        return copy.deepcopy(self._last_record)

    def apply_update(self, deltas: dict, *, baseline: float, episodes_seen: int) -> None:
        raise TypeError("use ThompsonLearner")


__all__ = ["N_MAX", "PRIOR_ALPHA", "PRIOR_BETA", "SELECTION_BASIS", "ThompsonPolicy", "replay", "seed_for"]
