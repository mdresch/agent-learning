"""Seeded, replayable draws for Thompson sampling (ADR-015, FDD-015).

Standard library only: nothing here reads the store or touches a file.
"""

from __future__ import annotations

import hashlib
import hmac
import random
from collections.abc import Mapping
from typing import Any


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


__all__ = ["replay", "seed_for"]
