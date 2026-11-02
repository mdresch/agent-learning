"""Contract tests for Epic 15, Story 15.1 (The Seed and the Replay).

Story: docs/user-stories/epic-15-bayesian-bandit-posterior-sampling.md, Story 15.1.
ADR-015 Invariants (replayable draws); BRD-015 BRU-015-02; FDD-015 §2.3 and §3 items 1 and 4.

Interpretation I1: ``choose`` is Story 15.3, so it cannot make the record yet. AC_3 builds the
record of FDD-015 §2.3 in the test with the same primitives ``choose`` uses (``seed_for`` and
``random.Random(seed).betavariate`` in snapshot order). Story 15.3 AC_2 asserts that a record
made by ``choose`` replays.

Interpretation I2: FDD-015 §3 item 4 re-derives the seed "from the record's request_id and
timestamp and the snapshot id", but the §2.3 record holds no policy id. ``replay`` therefore takes
the policy id as a second argument, ``replay(record, policy_id)``. The FDD should say so
(FDD-015 §7 item 6).

Interpretation I3: the draws are redrawn in the order of the record's ``posterior_parameters``
``alpha`` keys, which is snapshot order when ``choose`` made the record. A redraw that differs
from the recorded ``sampled_payoffs`` raises ``ValueError`` naming a version difference, not
tampering (FDD-015 §7 item 4).
"""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
import random

import pytest

from agent_learning.policy.thompson import replay, seed_for

POLICY_ID = "policy-1"
REQUEST_ID = "req-001"
TIMESTAMP = "2026-10-29T08:00:00+00:00"


def _expected_seed(policy_id: str, request_id: str, timestamp: str) -> int:
    digest = hmac.new(
        policy_id.encode("utf-8"),
        (request_id + "|" + timestamp).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return int(digest[:16], 16)


def _make_record() -> dict:
    """A FDD-015 §2.3 record, drawn the way ``choose`` draws (I1)."""
    posterior = {"alpha": {"a": 14.0, "b": 3.0}, "beta": {"a": 2.0, "b": 8.0}}
    seed = seed_for(POLICY_ID, REQUEST_ID, TIMESTAMP)
    rng = random.Random(seed)
    sampled = {a: rng.betavariate(posterior["alpha"][a], posterior["beta"][a]) for a in posterior["alpha"]}
    return {
        "request_id": REQUEST_ID,
        "timestamp": TIMESTAMP,
        "prng_seed": str(seed),
        "posterior_parameters": posterior,
        "sampled_payoffs": sampled,
    }


def test_ac0_seed_is_the_hmac_prefix_below_2_pow_64() -> None:
    seed = seed_for(POLICY_ID, REQUEST_ID, TIMESTAMP)
    assert seed == _expected_seed(POLICY_ID, REQUEST_ID, TIMESTAMP)
    assert 0 <= seed < 2**64


def test_ac1_seed_is_deterministic_and_sensitive_to_every_argument() -> None:
    base = seed_for(POLICY_ID, REQUEST_ID, TIMESTAMP)
    assert seed_for(POLICY_ID, REQUEST_ID, TIMESTAMP) == base

    variations = {
        seed_for("policy-2", REQUEST_ID, TIMESTAMP),
        seed_for(POLICY_ID, "req-002", TIMESTAMP),
        seed_for(POLICY_ID, REQUEST_ID, "2026-10-29T08:00:01+00:00"),
    }
    assert base not in variations
    assert len(variations) == 3

    assert seed_for(POLICY_ID, "ab", "c") != seed_for(POLICY_ID, "a", "bc")


@pytest.mark.parametrize(
    ("args", "name"),
    [
        (("", REQUEST_ID, TIMESTAMP), "policy_id"),
        ((POLICY_ID, "", TIMESTAMP), "request_id"),
        ((POLICY_ID, REQUEST_ID, ""), "timestamp"),
    ],
)
def test_ac2_empty_argument_is_refused_by_name(args: tuple[str, str, str], name: str) -> None:
    with pytest.raises(ValueError, match=name):
        seed_for(*args)


def test_ac3_replay_returns_the_recorded_draws_exactly() -> None:
    record = _make_record()
    assert replay(record, POLICY_ID) == record["sampled_payoffs"]

    # The record is a JSON document: it must replay after a round trip too.
    assert replay(json.loads(json.dumps(record)), POLICY_ID) == record["sampled_payoffs"]


def test_ac3_replay_refuses_a_seed_changed_by_one() -> None:
    record = _make_record()
    tampered = copy.deepcopy(record)
    tampered["prng_seed"] = str(int(record["prng_seed"]) + 1)
    with pytest.raises(ValueError, match="seed"):
        replay(tampered, POLICY_ID)


def test_ac3_replay_refuses_the_wrong_policy_id() -> None:
    with pytest.raises(ValueError, match="seed"):
        replay(_make_record(), "policy-2")


def test_ac3_replay_does_not_mutate_the_record() -> None:
    record = _make_record()
    before = copy.deepcopy(record)
    replay(record, POLICY_ID)
    assert record == before


def test_i3_changed_draw_is_reported_as_a_version_difference() -> None:
    record = _make_record()
    record["sampled_payoffs"]["a"] += 0.001
    with pytest.raises(ValueError, match="version"):
        replay(record, POLICY_ID)
