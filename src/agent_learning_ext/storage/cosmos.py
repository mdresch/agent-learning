"""Amended Cosmos store for agent_learning_ext (fork rule: Microsoft's ``storage/cosmos.py`` is not edited).

``CosmosStore`` here subclasses Microsoft's. ``store_policy`` writes the active-policy pointer with a monotonicity guard
(a lower version never replaces a higher one) and ETag optimistic concurrency with three retries (ADR-002 4.5, Story 2.1).

``get_default_store`` returns the same store as Microsoft's, except that the ``cosmos`` backend builds this class. It also
installs that store as Microsoft's process-wide singleton, so Microsoft's own callers (the reward writer) share it.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict
from urllib.parse import quote

from agent_learning.config import CosmosConfig
from agent_learning.storage import cosmos as _microsoft
from agent_learning.storage.base import LearningStore
from agent_learning.types import PolicySnapshot

cosmos_exceptions = _microsoft.cosmos_exceptions

try:
    from azure.core import MatchConditions  # type: ignore
except ImportError:  # pragma: no cover
    MatchConditions = None  # type: ignore

if cosmos_exceptions is not None:
    CosmosHttpResponseError = cosmos_exceptions.CosmosHttpResponseError
    CosmosResourceNotFoundError = cosmos_exceptions.CosmosResourceNotFoundError
    CosmosResourceExistsError = cosmos_exceptions.CosmosResourceExistsError
    CosmosAccessConditionFailedError = cosmos_exceptions.CosmosAccessConditionFailedError
else:
    class CosmosHttpResponseError(Exception):  # type: ignore[no-redef]
        def __init__(self, message: str = "", *args: Any, **kwargs: Any) -> None:
            super().__init__(message, *args)
            self.message = message

    class CosmosResourceNotFoundError(CosmosHttpResponseError):  # type: ignore[no-redef]
        pass

    class CosmosResourceExistsError(CosmosHttpResponseError):  # type: ignore[no-redef]
        pass

    class CosmosAccessConditionFailedError(CosmosHttpResponseError):  # type: ignore[no-redef]
        pass

    class _FakeCosmosExceptions:
        CosmosHttpResponseError = CosmosHttpResponseError
        CosmosResourceNotFoundError = CosmosResourceNotFoundError
        CosmosResourceExistsError = CosmosResourceExistsError
        CosmosAccessConditionFailedError = CosmosAccessConditionFailedError

    _microsoft.cosmos_exceptions = _FakeCosmosExceptions  # type: ignore


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


logger = logging.getLogger(__name__)


class CosmosStore(_microsoft.CosmosStore):
    """Microsoft's CosmosStore with the guarded, ETag-protected active-policy pointer."""

    def _read(self, key: str, item_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
        self._ensure_ready()
        try:
            return self._containers[key].read_item(item=item_id, partition_key=agent_id)
        except CosmosResourceNotFoundError:
            return None
        except CosmosHttpResponseError as exc:
            if getattr(exc, "status_code", None) == 404:
                return None
            logger.error("Cosmos read failed (%s/%s): %s", key, item_id, getattr(exc, "message", str(exc)))
            return None

    def _store_active_pointer(self, policy: PolicySnapshot, max_retries: int = 3) -> None:
        self._ensure_ready()
        container = self._containers["policies"]
        pointer_id = f"active:{quote(policy.task_id, safe='')}"

        for attempt in range(max_retries + 1):
            try:
                existing = self._read("policies", pointer_id, policy.agent_id)
                if existing is None:
                    pointer_doc = {
                        "id": pointer_id,
                        "agent_id": policy.agent_id,
                        "task_id": policy.task_id,
                        "policy_id": policy.id,
                        "policy_version": policy.version,
                        "record_type": "active_policy",
                        "updated_at": _utcnow_iso(),
                    }
                    container.create_item(pointer_doc)
                    return

                existing_version = existing.get("policy_version")
                if existing_version is None and existing.get("policy_id"):
                    existing_policy = self.get_policy(str(existing["policy_id"]), policy.agent_id)
                    if existing_policy is not None:
                        existing_version = existing_policy.version

                if existing_version is not None and existing_version > policy.version:
                    logger.warning(
                        "Active pointer for %s/%s already at higher version (%s > %s); skipping update",
                        policy.agent_id,
                        policy.task_id,
                        existing_version,
                        policy.version,
                    )
                    return

                if existing.get("policy_id") == policy.id and existing.get("policy_version") == policy.version:
                    return

                clean_existing = {k: v for k, v in existing.items() if not k.startswith("_")}
                pointer_doc = {
                    **clean_existing,
                    "policy_id": policy.id,
                    "policy_version": policy.version,
                    "updated_at": _utcnow_iso(),
                }
                etag = existing.get("_etag")
                replace_kwargs: Dict[str, Any] = {}
                if etag is not None:
                    replace_kwargs["etag"] = etag
                    if MatchConditions is not None:
                        replace_kwargs["match_condition"] = MatchConditions.IfNotModified
                container.replace_item(
                    item=pointer_id,
                    body=pointer_doc,
                    **replace_kwargs,
                )
                return
            except CosmosResourceExistsError:
                if attempt == max_retries:
                    raise
            except CosmosAccessConditionFailedError:
                if attempt == max_retries:
                    raise

    def store_policy(self, policy: PolicySnapshot) -> str:
        self._upsert("policies", policy.to_dict())
        self._store_active_pointer(policy)
        return policy.id


def get_default_store() -> LearningStore:
    """Microsoft's default store, except that the ``cosmos`` backend builds the amended CosmosStore."""
    if (
        _microsoft._default_store is None
        and os.getenv("AGENT_LEARNING_STORE_BACKEND", "memory").strip().lower() == "cosmos"
    ):
        cfg = CosmosConfig()
        if cfg.enabled and _microsoft.COSMOS_SDK_AVAILABLE:
            _microsoft._default_store = CosmosStore(cfg)
    return _microsoft.get_default_store()


__all__ = [
    "CosmosAccessConditionFailedError",
    "CosmosHttpResponseError",
    "CosmosResourceExistsError",
    "CosmosResourceNotFoundError",
    "CosmosStore",
    "get_default_store",
]
