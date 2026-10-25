# Lessons Learned Register (Organizational Process Assets)

**Governing ADR:** [ADR-010](../adr/ADR-010-lessons-learned-crystallization-and-register.md) — Accepted (2026-10-25)  
**Lifecycle Role:** Stage 15 Breakout & Recap Session (Post-Delivery Retrospective Notebook per ADR-008, ADR-009, ADR-010).  
**Maintenance Rule:** Append-only register. Crystallized entries represent verified institutional knowledge captured during post-delivery breakout pauses.

---

## Index of Crystallized Lessons

| ID | Title | Epic / Source | Tier Scope | Date |
|---|---|---|---|---|
| [LL-001](#ll-001--cosmos-db-read-only-system-properties-leak-into-replacement-bodies) | Cosmos DB Read-Only System Properties Leak into Replacement Bodies | Epic 2 / Story 2.1 | Universal Storage | 2026-10-25 |
| [LL-002](#ll-002--vacuous-assertions-on-exception-raising-datetime-parsers) | Vacuous Assertions on Exception-Raising Datetime Parsers | Epic 2 / Story 2.1 | Universal Testing | 2026-10-25 |
| [LL-003](#ll-003--module-level-exception-stubs-for-optional-cloud-sdks) | Module-Level Exception Stubs for Optional Cloud SDKs | Epic 2 / Story 2.1 | Repository Architecture | 2026-10-25 |
| [LL-004](#ll-004--closed-loop-interactive-ai-pr-review-via-q-protocol) | Closed-Loop Interactive AI PR Review via `/q` Protocol | Epic 2 / Story 2.1 | Universal Process | 2026-10-25 |

---

## Detailed Entries

### LL-001 — Cosmos DB Read-Only System Properties Leak into Replacement Bodies
- **Identifier:** `LL-001`
- **Date:** 2026-10-25
- **Epic / Story:** Epic 2 / Story 2.1 (PR [#4](https://github.com/mdresch/agent-learning/pull/4), commit `188ed8a`)
- **Scope:** Universal Storage (applies to Azure Cosmos DB, DocumentDB, and MongoDB APIs)
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/storage/SKILL.md` (enforced via `FakePoliciesContainer.replace_item`); Tier 3: `sidpa-template/storage/cosmos.py` and `RULE[user_global]`
- **The Trap:** When an existing document is retrieved from Cosmos DB via `read_item()`, Cosmos DB decorates the document with system-managed metadata fields (`_etag`, `_rid`, `_self`, `_ts`, `_attachments`). If the developer constructs an update using `{**existing, ...}` and submits it to `replace_item(body=...)`, these system fields are sent in the replacement payload. In production Cosmos DB or strict SDK environments, modifying read-only system properties triggers HTTP `400 Bad Request`.
- **The Root Cause:** Read payloads in Document databases mix user data with immutable engine metadata without separating them into distinct sub-dictionaries.
- **Actionable Invariant:** Always strip all `_`-prefixed keys before passing existing documents into write or replace calls:
  ```python
  clean_existing = {k: v for k, v in existing.items() if not k.startswith("_")}
  ```
- **Verification Gate:** Add an assertion in storage test mock containers (`FakePoliciesContainer.replace_item`) that fails immediately if any `_`-prefixed key is present in `body`.

---

### LL-002 — Vacuous Assertions on Exception-Raising Datetime Parsers
- **Identifier:** `LL-002`
- **Date:** 2026-10-25
- **Epic / Story:** Epic 2 / Story 2.1 (PR [#4](https://github.com/mdresch/agent-learning/pull/4), commit `188ed8a`)
- **Scope:** Universal Testing & Quality
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/storage/SKILL.md` & `tests/test_storage_cosmos.py`; Tier 3: `sidpa-template/testing/conventions.md`
- **The Trap:** Writing `assert dt is not None` after `dt = datetime.fromisoformat(payload["updated_at"])` produces a vacuous pass. `datetime.fromisoformat()` raises `ValueError` on malformed inputs and *never* returns `None`. Consequently, the actual acceptance criterion ($AC_0$: *timezone-aware UTC ISO 8601 string*) was completely unenforced by the test assertion.
- **The Root Cause:** Conflating operations that return `None` on failure with functions that raise exceptions on failure, creating an illusory green test.
- **Actionable Invariant:** Always test the domain properties of parsed objects rather than mere existence:
  ```python
  dt = datetime.fromisoformat(pointer["updated_at"])
  assert dt.tzinfo is not None, "Timestamp must be timezone-aware"
  assert dt.utcoffset() == timezone.utc.utcoffset(None), "Timestamp must be in UTC"
  ```

---

### LL-003 — Module-Level Exception Stubs for Optional Cloud SDKs
- **Identifier:** `LL-003`
- **Date:** 2026-10-25
- **Epic / Story:** Epic 2 / Story 2.1
- **Scope:** Repository Architecture (`agent_learning.storage`)
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/storage/SKILL.md`; Tier 3: `sidpa-template/storage/base.py`
- **The Trap:** An optional backend dependency (`azure-cosmos` in `[project.optional-dependencies]`) is imported under `try: ... except ImportError: cosmos_exceptions = None`. If internal helper methods or exception-handling blocks reference `except cosmos_exceptions.CosmosResourceNotFoundError:`, executing unit tests or mock stores in core development environments raises `AttributeError: 'NoneType' object has no attribute 'CosmosResourceNotFoundError'`.
- **The Root Cause:** Direct attribute lookups against a nullable module object inside class definitions and method signatures.
- **Actionable Invariant:** Define module-level fallback exception hierarchies when optional SDKs are missing:
  ```python
  if cosmos_exceptions is not None:
      CosmosHttpResponseError = cosmos_exceptions.CosmosHttpResponseError
      CosmosResourceNotFoundError = cosmos_exceptions.CosmosResourceNotFoundError
      CosmosResourceExistsError = cosmos_exceptions.CosmosResourceExistsError
      CosmosAccessConditionFailedError = cosmos_exceptions.CosmosAccessConditionFailedError
  else:
      class CosmosHttpResponseError(Exception):
          def __init__(self, message: str = "", *args: Any, **kwargs: Any) -> None:
              super().__init__(message, *args)
              self.message = message
      class CosmosResourceNotFoundError(CosmosHttpResponseError): pass
      class CosmosResourceExistsError(CosmosHttpResponseError): pass
      class CosmosAccessConditionFailedError(CosmosHttpResponseError): pass
  ```
  This guarantees that all storage methods and unit test mocks catch and raise standardized exceptions identically regardless of installed extras.

---

### LL-004 — Closed-Loop Interactive AI PR Review via `/q` Protocol
- **Identifier:** `LL-004`
- **Date:** 2026-10-25
- **Epic / Story:** Epic 2 / Story 2.1 (PR [#4](https://github.com/mdresch/agent-learning/pull/4))
- **Scope:** Universal Process & CI/CD Governance
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 8); Tier 3: `sidpa-template/governance/pr_workflow.md`
- **The Trap:** External AI reviewers (e.g. Amazon Q Developer) post PR review comments, but without a standard interaction protocol, human developers either ignore the bot comments or manually debate them without a verifiable re-evaluation.
- **The Root Cause:** Lack of an explicit, auditable command-driven handoff loop between automated reviewers and coding agents.
- **Actionable Invariant:** 
  1. Address review items with dedicated commits.
  2. Comment on the PR using `/q <instructions>` to trigger an automated re-review pass by the bot.
  3. Merge only after the automated reviewer issues an explicit positive verdict (e.g., *"Overall verdict: all substantive previous review findings are resolved in this commit"*).
  4. Record the review-to-merge trajectory in the implementation and lessons-learned logs.

