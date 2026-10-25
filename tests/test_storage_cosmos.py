"""Contract tests for CosmosStore active-policy pointer concurrency protection.

Derived from ADR-002 §4.5, BRD-002, and FDD-002 (Story 2.1).
Acceptance Criteria:
- AC-0: Pointer schema enrichment (policy_version, updated_at in ISO 8601 UTC).
- AC-1: Monotonicity guard blocks older version regression.
- AC-2: ETag optimistic concurrency on pointer replacement with 3-retry backoff.
- AC-3: Racing initial creation retries via update path on CosmosResourceExistsError.
- AC-4: get_active_policy backward compatibility across legacy and enhanced pointers.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest

import agent_learning.storage.cosmos as cosmos_mod
from agent_learning.config import CosmosConfig
from agent_learning.storage.cosmos import (
    CosmosAccessConditionFailedError,
    CosmosResourceExistsError,
    CosmosResourceNotFoundError,
    CosmosStore,
)
from agent_learning.types import PolicySnapshot

try:
    from azure.core import MatchConditions
except ImportError:
    MatchConditions = None


class FakePoliciesContainer:
    """In-memory mock for Cosmos policies container supporting ETag and concurrency semantics."""

    def __init__(self) -> None:
        self.items: Dict[str, Dict[str, Any]] = {}
        self.create_item_calls: List[Dict[str, Any]] = []
        self.replace_item_calls: List[Dict[str, Any]] = []
        self.upsert_item_calls: List[Dict[str, Any]] = []
        self.create_item_side_effect: Optional[Exception] = None
        self.replace_item_side_effects: List[Optional[Exception]] = []

    def create_item(self, body: Dict[str, Any]) -> Dict[str, Any]:
        self.create_item_calls.append(body)
        if self.create_item_side_effect:
            exc = self.create_item_side_effect
            self.create_item_side_effect = None
            raise exc

        item_id = body["id"]
        if item_id in self.items:
            raise CosmosResourceExistsError(f"Resource already exists: {item_id}")

        doc = dict(body)
        doc["_etag"] = f"etag_{len(self.items) + 1}"
        self.items[item_id] = doc
        return doc

    def replace_item(
        self,
        item: str,
        body: Dict[str, Any],
        *,
        etag: Optional[str] = None,
        match_condition: Optional[Any] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        call_record = {
            "item": item,
            "body": body,
            "etag": etag,
            "match_condition": match_condition,
            **kwargs,
        }
        self.replace_item_calls.append(call_record)

        if self.replace_item_side_effects:
            effect = self.replace_item_side_effects.pop(0)
            if effect is not None:
                raise effect

        if item not in self.items:
            raise CosmosResourceNotFoundError(f"Item not found: {item}")

        current = self.items[item]
        if etag is not None and current.get("_etag") != etag:
            raise CosmosAccessConditionFailedError(f"ETag mismatch: {etag} vs {current.get('_etag')}")

        doc = dict(body)
        doc["_etag"] = f"etag_{len(self.replace_item_calls) + 100}"
        self.items[item] = doc
        return doc

    def upsert_item(self, body: Dict[str, Any]) -> Dict[str, Any]:
        self.upsert_item_calls.append(body)
        item_id = body["id"]
        doc = dict(body)
        doc["_etag"] = f"etag_{len(self.items) + 1}"
        self.items[item_id] = doc
        return doc

    def read_item(self, item: str, partition_key: str) -> Dict[str, Any]:
        if item not in self.items:
            raise CosmosResourceNotFoundError(f"Not found: {item}")
        return dict(self.items[item])

    def query_items(self, query: str, parameters: Optional[List[Dict[str, Any]]] = None, **kwargs: Any):
        # Return all non-pointer policy snapshot items
        results = [
            doc for doc in self.items.values()
            if not doc.get("record_type")
        ]
        return iter(results)


@pytest.fixture
def store_fixture():
    """Build an initialized CosmosStore wired to FakePoliciesContainer."""
    config = CosmosConfig(endpoint="https://fake.documents.azure.com:443/")
    store = CosmosStore(config=config)
    store._initialized = True
    fake_container = FakePoliciesContainer()
    store._containers = {"policies": fake_container}
    return store, fake_container


def test_ac0_active_pointer_has_version_and_timestamp(store_fixture):
    """AC_0: store_policy writes pointer with policy_version and updated_at ISO UTC."""
    store, container = store_fixture
    policy = PolicySnapshot(
        id="policy-v1",
        agent_id="agent-alpha",
        task_id="task-sort",
        version=1,
    )

    store.store_policy(policy)

    pointer = container.items.get("active:task-sort")
    assert pointer is not None, "Active pointer document active:task-sort was not created"
    assert pointer["agent_id"] == "agent-alpha"
    assert pointer["task_id"] == "task-sort"
    assert pointer["policy_id"] == "policy-v1"
    assert pointer["record_type"] == "active_policy"
    assert pointer["policy_version"] == 1
    assert "updated_at" in pointer
    # Must be valid ISO 8601 UTC timestamp
    dt = datetime.fromisoformat(pointer["updated_at"])
    assert dt is not None


def test_ac1_monotonicity_guard_blocks_older_version_regression(store_fixture, caplog):
    """AC_1: Candidate with lower version does not overwrite newer active pointer."""
    store, container = store_fixture

    # Existing active pointer at version 3
    container.items["active:task-sort"] = {
        "id": "active:task-sort",
        "agent_id": "agent-alpha",
        "task_id": "task-sort",
        "policy_id": "policy-v3",
        "policy_version": 3,
        "record_type": "active_policy",
        "updated_at": "2026-10-25T12:00:00+00:00",
        "_etag": "etag-v3",
    }

    # Candidate snapshot at version 2
    policy_v2 = PolicySnapshot(
        id="policy-v2",
        agent_id="agent-alpha",
        task_id="task-sort",
        version=2,
    )

    with caplog.at_level(logging.WARNING):
        returned_id = store.store_policy(policy_v2)

    # 1. Candidate snapshot itself must be stored safely
    assert returned_id == "policy-v2"
    assert "policy-v2" in container.items

    # 2. Pointer document must NOT regress to version 2
    pointer = container.items["active:task-sort"]
    assert pointer["policy_id"] == "policy-v3"
    assert pointer["policy_version"] == 3

    # 3. Warning must be logged
    assert any("already at higher version" in msg for msg in caplog.messages)


def test_ac2_etag_concurrency_replace_with_retry(store_fixture):
    """AC_2: replace_item uses ETag and retries up to 3 times on CosmosAccessConditionFailedError."""
    store, container = store_fixture

    container.items["active:task-sort"] = {
        "id": "active:task-sort",
        "agent_id": "agent-alpha",
        "task_id": "task-sort",
        "policy_id": "policy-v1",
        "policy_version": 1,
        "record_type": "active_policy",
        "updated_at": "2026-10-25T11:00:00+00:00",
        "_etag": "etag-initial",
    }

    # Simulate 2 transient ETag conflicts, then succeed on 3rd attempt
    container.replace_item_side_effects = [
        CosmosAccessConditionFailedError("ETag mismatch attempt 1"),
        CosmosAccessConditionFailedError("ETag mismatch attempt 2"),
        None,  # Success
    ]

    policy_v2 = PolicySnapshot(
        id="policy-v2",
        agent_id="agent-alpha",
        task_id="task-sort",
        version=2,
    )

    returned_id = store.store_policy(policy_v2)
    assert returned_id == "policy-v2"

    pointer = container.items["active:task-sort"]
    assert pointer["policy_id"] == "policy-v2"
    assert pointer["policy_version"] == 2
    assert len(container.replace_item_calls) == 3

    # Check that match condition and ETag were passed
    first_call = container.replace_item_calls[0]
    assert first_call["etag"] == "etag-initial"
    if MatchConditions is not None:
        assert first_call["match_condition"] == MatchConditions.IfNotModified


def test_ac2_etag_concurrency_retry_exhaustion_raises(store_fixture):
    """AC_2: If ETag conflict persists past max_retries (3 retries = 4 attempts), error is raised."""
    store, container = store_fixture

    container.items["active:task-sort"] = {
        "id": "active:task-sort",
        "agent_id": "agent-alpha",
        "task_id": "task-sort",
        "policy_id": "policy-v1",
        "policy_version": 1,
        "record_type": "active_policy",
        "updated_at": "2026-10-25T11:00:00+00:00",
        "_etag": "etag-initial",
    }

    # 4 consecutive conflicts
    container.replace_item_side_effects = [
        CosmosAccessConditionFailedError("Conflict 1"),
        CosmosAccessConditionFailedError("Conflict 2"),
        CosmosAccessConditionFailedError("Conflict 3"),
        CosmosAccessConditionFailedError("Conflict 4"),
    ]

    policy_v2 = PolicySnapshot(
        id="policy-v2",
        agent_id="agent-alpha",
        task_id="task-sort",
        version=2,
    )

    with pytest.raises(CosmosAccessConditionFailedError):
        store.store_policy(policy_v2)


def test_ac3_create_pointer_retries_on_resource_exists_conflict(store_fixture):
    """AC_3: Racing initial creations raising CosmosResourceExistsError retry via update path."""
    store, container = store_fixture

    # Initially empty container (pointer does not exist)
    # But when store attempts create_item, race condition triggers CosmosResourceExistsError
    def race_create(body):
        # Another process just wrote it
        container.items[body["id"]] = {
            "id": body["id"],
            "agent_id": body["agent_id"],
            "task_id": body["task_id"],
            "policy_id": "policy-v1",
            "policy_version": 1,
            "record_type": "active_policy",
            "updated_at": "2026-10-25T11:00:00+00:00",
            "_etag": "etag-race",
        }
        raise CosmosResourceExistsError("Resource exists race")

    container.create_item_side_effect = CosmosResourceExistsError("Item already exists")

    # Manually populate on first failure to mimic concurrent process
    old_create = container.create_item
    def patched_create(body):
        container.items[body["id"]] = {
            "id": body["id"],
            "agent_id": body["agent_id"],
            "task_id": body["task_id"],
            "policy_id": "policy-v1",
            "policy_version": 1,
            "record_type": "active_policy",
            "updated_at": "2026-10-25T11:00:00+00:00",
            "_etag": "etag-race",
        }
        raise CosmosResourceExistsError("Item already exists")

    container.create_item = patched_create

    policy_v2 = PolicySnapshot(
        id="policy-v2",
        agent_id="agent-alpha",
        task_id="task-sort",
        version=2,
    )

    store.store_policy(policy_v2)

    pointer = container.items["active:task-sort"]
    assert pointer["policy_id"] == "policy-v2"
    assert pointer["policy_version"] == 2
    assert len(container.replace_item_calls) >= 1


def test_ac4_get_active_policy_resolves_legacy_and_enhanced_pointers(store_fixture):
    """AC_4: get_active_policy resolves active policies across legacy and enhanced pointers."""
    store, container = store_fixture

    p1 = PolicySnapshot(id="p1", agent_id="agent-1", task_id="task-1", version=1)
    p2 = PolicySnapshot(id="p2", agent_id="agent-1", task_id="task-2", version=2)
    container.items["p1"] = p1.to_dict()
    container.items["p2"] = p2.to_dict()

    # Legacy pointer for task-1 (lacks policy_version, updated_at)
    container.items["active:task-1"] = {
        "id": "active:task-1",
        "agent_id": "agent-1",
        "task_id": "task-1",
        "policy_id": "p1",
        "record_type": "active_policy",
    }

    # Enhanced pointer for task-2
    container.items["active:task-2"] = {
        "id": "active:task-2",
        "agent_id": "agent-1",
        "task_id": "task-2",
        "policy_id": "p2",
        "policy_version": 2,
        "record_type": "active_policy",
        "updated_at": "2026-10-25T12:00:00+00:00",
    }

    resolved_1 = store.get_active_policy("agent-1", "task-1")
    assert resolved_1 is not None
    assert resolved_1.id == "p1"
    assert resolved_1.version == 1

    resolved_2 = store.get_active_policy("agent-1", "task-2")
    assert resolved_2 is not None
    assert resolved_2.id == "p2"
    assert resolved_2.version == 2


def test_monotonicity_guard_with_legacy_pointer(store_fixture, caplog):
    """Legacy pointer lacking policy_version falls back to inspecting policy snapshot."""
    store, container = store_fixture

    p_old = PolicySnapshot(id="p-old-v5", agent_id="agent-1", task_id="task-legacy", version=5)
    container.items["p-old-v5"] = p_old.to_dict()

    # Legacy pointer without policy_version
    container.items["active:task-legacy"] = {
        "id": "active:task-legacy",
        "agent_id": "agent-1",
        "task_id": "task-legacy",
        "policy_id": "p-old-v5",
        "record_type": "active_policy",
        "_etag": "etag-legacy",
    }

    # Candidate with lower version
    p_candidate = PolicySnapshot(id="p-candidate-v3", agent_id="agent-1", task_id="task-legacy", version=3)

    with caplog.at_level(logging.WARNING):
        store.store_policy(p_candidate)

    pointer = container.items["active:task-legacy"]
    assert pointer["policy_id"] == "p-old-v5"
    assert any("already at higher version" in msg for msg in caplog.messages)
