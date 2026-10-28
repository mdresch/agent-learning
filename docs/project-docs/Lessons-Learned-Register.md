# Lessons Learned Register (Organizational Process Assets)

**Governing ADR:** [ADR-010](../adr/ADR-010-lessons-learned-crystallization-and-register.md) — Accepted (2026-10-25)  
**Lifecycle Role:** Light post-coding breakout recap per ADR-010: held once per epic, after its last user story, on how the code was created from the stories. Not the formal Stage 15 review, which is separate.  
**Maintenance Rule:** Append-only register. Crystallized entries represent verified institutional knowledge captured at the epic-end recap. A recap with nothing new is recorded as a short sign-off entry (Epic/Phase containing `no-new-lessons`).  
**Cadence note:** `LL-001` through `LL-006` were recorded per story, before ADR-010 was clarified to a per-epic cadence (2026-10-25). New entries follow the epic-end cadence.

---

## Index of Crystallized Lessons

| ID | Title | Epic / Source | Tier Scope | Date |
|---|---|---|---|---|
| [LL-001](#ll-001--cosmos-db-read-only-system-properties-leak-into-replacement-bodies) | Cosmos DB Read-Only System Properties Leak into Replacement Bodies | Epic 2 / Story 2.1 | Universal Storage | 2026-10-25 |
| [LL-002](#ll-002--vacuous-assertions-on-exception-raising-datetime-parsers) | Vacuous Assertions on Exception-Raising Datetime Parsers | Epic 2 / Story 2.1 | Universal Testing | 2026-10-25 |
| [LL-003](#ll-003--module-level-exception-stubs-for-optional-cloud-sdks) | Module-Level Exception Stubs for Optional Cloud SDKs | Epic 2 / Story 2.1 | Repository Architecture | 2026-10-25 |
| [LL-004](#ll-004--closed-loop-interactive-ai-pr-review-via-q-protocol) | Closed-Loop Interactive AI PR Review via `/q` Protocol | Epic 2 / Story 2.1 | Universal Process | 2026-10-25 |
| [LL-005](#ll-005--compound-header--delimiter-bleed-in-markdown-parsers) | Compound Header & Delimiter Bleed in Markdown Parsers | Epic 10 / Story 10.1 | Universal Tooling | 2026-10-25 |
| [LL-006](#ll-006--cwd-independent-path-anchoring-in-test-suites) | CWD-Independent Path Anchoring in Test Suites | Epic 10 / Story 10.1 | Universal Testing | 2026-10-25 |
| [LL-007](#ll-007--counts-and-pending-notes-go-stale-in-the-change-that-resolves-them) | Counts and Pending Notes Go Stale in the Change That Resolves Them | Epic 10 / PR #6 | Universal Documentation | 2026-10-25 |
| [LL-008](#ll-008--keep-only-hardened-decisions-in-an-adr) | Keep Only Hardened Decisions in an ADR | Epic 11 / ADR-011 | Repository Process | 2026-10-25 |
| [LL-009](#ll-009--verify-the-edition-of-a-standard-before-citing-it) | Verify the Edition of a Standard Before Citing It | Epic 11 / ADR-011, ADR-008 | Universal Documentation | 2026-10-25 |
| [LL-010](#ll-010--implement-only-against-approved-committed-specs) | Implement Only Against Approved, Committed Specs | Epic 11 / Stories 11.1, 11.2 | Repository Process | 2026-10-25 |
| [LL-011](#ll-011--state-every-mode-and-parameter-in-the-fdd) | State Every Mode and Parameter in the FDD | Epic 11 / FDD-011, Story 11.2 | Universal Design & Testing | 2026-10-25 |
| [LL-012](#ll-012--state-each-rule-in-one-storys-acceptance-criteria) | State Each Rule in One Story's Acceptance Criteria | Epic 11 / Stories 11.1, 11.2 | Universal Testing | 2026-10-25 |
| [LL-013](#ll-013--keep-a-skills-validation-command-one-that-runs) | Keep a Skill's Validation Command One That Runs | Epic 11 / implement-story skill | Universal Process | 2026-10-25 |
| [LL-014](#ll-014--define-blank-once-and-test-every-container-type) | Define Blank Once and Test Every Container Type | Epic 11 / Stories 11.1, 11.2 | Universal Code Quality | 2026-10-25 |
| [LL-015](#ll-015--monolithic-integrated-gates-obscure-component-level-credit-assignment) | Monolithic Integrated Gates Obscure Component-Level Credit Assignment | ADR-013 / PMBOK Orchestration | Universal Governance & Architecture | 2026-10-25 |
| [LL-016](#ll-016--a-review-command-must-start-its-own-comment) | A Review Command Must Start Its Own Comment | Epic 36 / Stories 36.3 to 36.5 | Universal Process | 2026-10-26 |
| [LL-017](#ll-017--a-package-root-re-export-can-shadow-an-existing-name) | A Package-Root Re-Export Can Shadow an Existing Name | Epic 36 / Story 36.5 | Universal Code Quality | 2026-10-26 |
| [LL-018](#ll-018--name-the-target-repository-on-every-pr-command) | Name the Target Repository on Every PR Command | Epic 36 / Story 36.3 | Universal Process | 2026-10-26 |
| [LL-019](#ll-019--evidence-must-be-unambiguous-in-its-own-representation) | Evidence Must Be Unambiguous in Its Own Representation | Epic 36 / Story 36.3 | Universal Review | 2026-10-26 |
| [LL-020](#ll-020--read-a-mutable-global-once) | Read a Mutable Global Once | Epic 3 / Story 3.1 | Universal Code Quality | 2026-10-26 |
| [LL-021](#ll-021--read-a-posted-command-back-before-trusting-a-reply) | Read a Posted Command Back Before Trusting a Reply | Epic 3 / Story 3.1 | Universal Process | 2026-10-26 |
| [LL-022](#ll-022--a-normative-pattern-must-be-run-not-paraphrased) | A Normative Pattern Must Be Run, Not Paraphrased | Epic 12 / Story 12.3 | Universal Testing | 2026-10-27 |
| [LL-023](#ll-023--never-read-a-document-at-import-time-in-a-test-file) | Never Read a Document at Import Time in a Test File | Epic 12 / Stories 12.1 and 12.3 | Universal Testing | 2026-10-27 |
| [LL-024](#ll-024--check-what-an-acceptance-criterion-leans-on-before-scoring-a-gate) | Check What an Acceptance Criterion Leans On Before Scoring a Gate | Epic 12 / Story 12.2 | Universal Process | 2026-10-27 |
| [LL-025](#ll-025--shell-heredocs-and-tool-inputs-change-backslashes) | Shell Heredocs and Tool Inputs Change Backslashes | Epic 12 / Story 12.3 | Universal Tooling | 2026-10-27 |
| [LL-026](#ll-026--do-not-run-an-auto-fixer-on-files-outside-your-change) | Do Not Run an Auto-Fixer on Files Outside Your Change | Epic 12 / Story 12.4 | Universal Tooling | 2026-10-27 |
| [LL-027](#ll-027--approvals-must-be-committed-before-the-code-they-gate) | Approvals Must Be Committed Before the Code They Gate | Epic 13 / Stories 13.1–13.7 | Universal Process | 2026-10-28 |
| [LL-028](#ll-028--an-unloaded-skill-is-not-followed) | An Unloaded Skill Is Not Followed | Epic 13 / Stories 13.1–13.7 | Universal Process | 2026-10-28 |
| [LL-029](#ll-029--do-not-use-python-hash-in-tests) | Do Not Use Python `hash()` in Tests | Epic 13 / Stories 13.1–13.7 | Universal Testing | 2026-10-28 |
| [LL-030](#ll-030--a-missing-tool-is-not-a-skipped-gate) | A Missing Tool Is Not a Skipped Gate | Epic 13 / Stories 13.1–13.7 | Universal Tooling | 2026-10-28 |
| [LL-031](#ll-031--triage-a-reviewers-confirmation-too) | Triage a Reviewer's Confirmation Too | Epic 13 / Stories 13.1–13.7 | Universal Process | 2026-10-28 |
| [LL-032](#ll-032--check-for-an-omission-without-a-filter) | Check for an Omission Without a Filter | Epic 13 / Stories 13.1–13.7 | Universal Process | 2026-10-28 |

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



---

### LL-005 — Compound Header & Delimiter Bleed in Markdown Parsers
- **Identifier:** `LL-005`
- **Date:** 2026-10-25
- **Epic / Story:** Epic 10 / Story 10.1 (PR [#5](https://github.com/mdresch/agent-learning/pull/5))
- **Scope:** Universal Tooling (markdown parsing & ingestion)
- **Tier 2/3 Propagation Target:** Tier 2: `src/agent_learning/lessons_learned.py`; Tier 3: `sidpa-template/parsers/markdown.py`
- **The Trap:** When supporting human-friendly compound markdown fields (such as `- **Date & Phase:** 2026-10-25 · Epic 2`), naively assigning the raw field string to `phase` causes the date prefix to bleed into the phase value (`"2026-10-25 · Epic 2"`). Loose tests that only assert substring containment (`"Epic 2" in phase`) pass coincidentally, concealing the data corruption from exact-match downstream consumers.
- **The Root Cause:** Assigning composite raw string tokens into discrete domain model fields without boundary isolation.
- **Actionable Invariant:** Always tokenize compound header fields on the designated delimiter (`·`, `-`, `/`) and assign discrete fields independently:
  ```python
  if "date & phase" in field_map:
      parts = [p.strip() for p in field_map["date & phase"].split("·", 1)]
      if not date:
          date = parts[0]
      if not phase and len(parts) > 1:
          phase = parts[1]
  ```

---

### LL-006 — CWD-Independent Path Anchoring in Test Suites
- **Identifier:** `LL-006`
- **Date:** 2026-10-25
- **Epic / Story:** Epic 10 / Story 10.1 (PR [#5](https://github.com/mdresch/agent-learning/pull/5))
- **Scope:** Universal Testing & CI Rigor
- **Tier 2/3 Propagation Target:** Tier 2: `tests/test_lessons_learned.py`; Tier 3: `sidpa-template/testing/conventions.md`
- **The Trap:** Using relative working-directory paths like `Path("docs/project-docs/Lessons-Learned-Register.md")` inside unit or contract tests works only when pytest is run from the workspace root. When tests run from subdirectories, IDE test runners, or multi-workspace CI matrix runners, the test fails with a false `FileNotFoundError` or assertion failure.
- **The Root Cause:** Implicit coupling of file fixture resolution to process execution CWD (`os.getcwd()`).
- **Actionable Invariant:** Always anchor repository asset paths relative to `__file__`:
  ```python
  repo_root = Path(__file__).resolve().parent.parent
  register_path = repo_root / "docs" / "project-docs" / "Lessons-Learned-Register.md"
  ```

---

### LL-007 — Counts and Pending Notes Go Stale in the Change That Resolves Them
- **Identifier:** `LL-007`
- **Date:** 2026-10-25
- **Epic / Story:** Epic 10 / PR [#6](https://github.com/mdresch/agent-learning/pull/6)
- **Scope:** Universal Documentation & Process
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 6); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** A documentation PR added a Step 9 to the `implement-story` loop but left "Steps 0-8" in the skill's front-matter description and its intro sentence. The same PR completed a re-wording that ADR-010 §4.6 still described as pending ("must be reworded"). A BRD metric kept targeting `LL-001` through `LL-004` after the register grew to `LL-006`. Automated review (Q Developer) caught all three after the PR was opened; none was caught by the test suite.
- **The Root Cause:** The same fact (a loop length, a lesson count, the status of a pending action) was written by hand in several places. The change that made it false only touched the place the author was looking at. Prose has no test, and a front-matter description is read by tools that never reach the body.
- **Actionable Invariant:** When a change adds a step or entry, changes a count, or completes an action another document calls pending, search the repository for the old number or phrase and update every occurrence in the same change. Prefer wording that cannot go stale ("at least", or a reference to the source) over a hard-coded total:
  ```bash
  rg "Steps 0|steps 0-8|must be reworded|LL-001. through" docs .claude
  ```

---

### LL-008 — Keep Only Hardened Decisions in an ADR
- **Identifier:** `LL-008`
- **Date:** 2026-10-25
- **Epic / Story:** Epic 11 / ADR-011 (docs branch; PRs [#7](https://github.com/mdresch/agent-learning/pull/7), [#8](https://github.com/mdresch/agent-learning/pull/8))
- **Scope:** Repository Process (ADR authoring)
- **Tier 2/3 Propagation Target:** Tier 1 only; candidate Tier 2: an ADR-authoring convention in `docs/adr/README.md` (proposed, needs human confirmation)
- **The Trap:** The first ADR-011 draft folded every confirmed clarification into one document (Charter contents, approval limits, ownership, learners, burden figures, the PMBOK mapping) and grew to about 190 lines, with each revision and each external review adding more. Slimming it to a small ADR then dropped the Alternatives section, which `approve-adr` scores as `alternatives_considered`, and a reviewer had to point out the loss.
- **The Root Cause:** Confirmed clarifications were consolidated into the ADR as they arrived, which treated working design as decided design. The later trim removed content without checking what the approval policy scores.
- **Actionable Invariant:** An ADR records only decisions that have been confirmed repeatedly; provisional design lives in working notes until it hardens. Before shortening an ADR, read the approval criteria (architectural soundness, alternatives considered, consequences honest, gap disclosure) and keep what they score. The BRD, FDD and stories then derive only from the ADR's Decisions and Invariants and list everything deferred as out of scope.

---

### LL-009 — Verify the Edition of a Standard Before Citing It
- **Identifier:** `LL-009`
- **Date:** 2026-10-25
- **Epic / Story:** Epic 11 / ADR-011 and ADR-008 (labels)
- **Scope:** Universal Documentation
- **Tier 2/3 Propagation Target:** Tier 1 only; follow-up decision needed on relabelling "PMBOK 8" in ADR-008 and the chain documents
- **The Trap:** ADR-008, the process registry and the chain documents say "PMBOK 8" but use 6th-edition numbering and plan names (a 49-process graph, 4.x numbers, cost and procurement plans), while the 8th edition has seven performance domains and different names. This surfaced only when the licensed 8th-edition text was pasted in. Web search results were secondary sources and could not settle it.
- **The Root Cause:** The edition was named from the label already on the project documents and was never checked against the standard itself.
- **Actionable Invariant:** When an ADR, BRD or FDD cites a standard, record the edition and the section numbers, verified against the primary source, and mark anything taken from a secondary source as unverified. Do not copy licensed text into the repository: paraphrase and cite section numbers.

---

### LL-010 — Implement Only Against Approved, Committed Specs
- **Identifier:** `LL-010`
- **Date:** 2026-10-25
- **Epic / Story:** Epic 11 / Stories 11.1 and 11.2
- **Scope:** Repository Process
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Steps 0 and 1); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** Story implementation started on a BRD, FDD and stories that were the author's own drafts: uncommitted, and without the `approve-brd`, `approve-fdd` and `approve-user-stories` gates run. "Status: Ready" had been set by the author, not by an approval. The approvals were recorded later in another checkout, after the worktrees had forked, so the story branches carried the draft specs and had to be reconciled by committing and merging.
- **The Root Cause:** The run began on a general go-ahead without checking the chain's order (approved requirements at Stage 7 before delivery at Stage 9), and a git worktree forks from committed state only.
- **Actionable Invariant:** Approve, then commit, then fork. Before `git worktree add`, confirm that the story's BRD, FDD and stories are approved and run `git status --short` in the base checkout. If the specs change after the fork, merge the base into the story branch before the PR. A "Ready" status set by the author is not an approval.

---

### LL-011 — State Every Mode and Parameter in the FDD
- **Identifier:** `LL-011`
- **Date:** 2026-10-25
- **Epic / Story:** Epic 11 / FDD-011 and Story 11.2 (PR [#8](https://github.com/mdresch/agent-learning/pull/8))
- **Scope:** Universal Design & Testing
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 3); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** FDD-011 gave `resolve_home` a signature and a one-line granularity rule but was silent on what `conflict` means in section mode, and it did not list the `elements` argument the code needed. A contract test encoded one reading of an open ADR question, and the automated reviewer called it a bug in the code.
- **The Root Cause:** The design left an edge mode and a parameter unspecified, so the implementation and its test filled the gap without marking it as a choice.
- **Actionable Invariant:** The FDD states the semantics and signature of every mode and parameter, and marks behavior that depends on an open ADR question as provisional. Anything added at implementation time is recorded as an interpretation in the test docstring and the log, and amended into the FDD or the open questions.

---

### LL-012 — State Each Rule in One Story's Acceptance Criteria
- **Identifier:** `LL-012`
- **Date:** 2026-10-25
- **Epic / Story:** Epic 11 / Stories 11.1 and 11.2
- **Scope:** Universal Testing
- **Tier 2/3 Propagation Target:** Tier 1 only; candidate guidance for `approve-user-stories` (proposed, needs human confirmation)
- **The Trap:** Story 11.2's AC_2 ("an accepted flagged route needs a rationale") restated Story 11.1's rule that every decided route needs a rationale. Its test passed on arrival, so the RED step could not be observed and the log had to explain the exception.
- **The Root Cause:** A rule shared by two stories was written into both sets of criteria instead of one, so the second contract asserted behavior that already existed.
- **Actionable Invariant:** Each rule lives in exactly one story's acceptance criteria. Later stories reference it and assert only what is new (for example, that the flag codes appear in the episode metadata), so that every contract can be observed failing first.

---

### LL-013 — Keep a Skill's Validation Command One That Runs
- **Identifier:** `LL-013`
- **Date:** 2026-10-25
- **Epic / Story:** Epic 11 / `implement-story` skill (Stories 11.1 and 11.2)
- **Scope:** Universal Process
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 6); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** The `implement-story` skill requires "the full suite passes", but 15 files under `tests/pmbok` cannot be collected from a clean install, so the command cannot pass. An earlier log entry reported 464 passed "across entire agent-learning test suite" without saying those files were excluded. The arithmetic (464 + 10 = 474) only matched after this epic's tests were added.
- **The Root Cause:** The skill's command described the intended state rather than the one that runs, and the log did not record what the count excluded.
- **Actionable Invariant:** Keep the skill's validation command accurate: fix the cause (declare the dependencies) or amend the command. Until then, record in the log which paths were excluded, why, and the resulting count, and never call an exclusion-adjusted count the entire suite.

---

### LL-014 — Define Blank Once and Test Every Container Type
- **Identifier:** `LL-014`
- **Date:** 2026-10-25
- **Epic / Story:** Epic 11 / Stories 11.1 and 11.2 (PRs [#7](https://github.com/mdresch/agent-learning/pull/7), [#8](https://github.com/mdresch/agent-learning/pull/8))
- **Scope:** Universal Code Quality
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/tailoring/SKILL.md`; Tier 3: `sidpa-template` testing conventions (proposed, needs human approval before any cross-repo change)
- **The Trap:** Automated review found that `_defined` treated empty tuples, sets and frozensets as defined (only `[]` and `{}` were excluded) and that one validation check combined two conditions in a single error message. Both were reachable through the public `Any` contract.
- **The Root Cause:** Blank detection was written from the examples at hand, and two conditions shared one branch.
- **Actionable Invariant:** For `Any`-typed inputs, define "blank" in one helper that covers `None`, blank strings and every empty container type, and test each one. Use one condition per error message so the message names what is actually missing.

---

### LL-015 — Monolithic Integrated Gates Obscure Component-Level Credit Assignment
- **Identifier:** `LL-015`
- **Date:** 2026-10-25
- **Epic / Story:** ADR-013 / PMBOK Orchestration
- **Scope:** Universal Governance & Architecture
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/learning-methodology-selection/SKILL.md`; Tier 3: `sidpa-template` PMBOK orchestration and governance rules
- **The Trap:** When multiple generative components (e.g., nine subsidiary management plans) are synthesized into a single monolithic composite document (e.g., the integrated PMP) before evaluation, a rejection or revision request at the composite gate cannot be localized to a specific component. Maintainers must conduct an exhaustive manual diagnostic search across all components. Worse, stub or failed components slip into formal baseline labels undetected because individual components were never governed.
- **The Root Cause:** Multi-input single-output (MIMO) evaluation conflates individual component deficiencies with cross-cutting integration conflicts.
- **Actionable Invariant:** Every component destined for a baseline must pass an individual, hash-verified, route-aware approval gate before composite formalization. Decouple **Component-Level Defects** (governed at the component gate) from **Integration-Level Defects** (governed at the composite synthesis gate).
- **Verification Gate:** Formalization steps must assert that every constituent component satisfies its route contract (e.g. hash match, non-stub) and carries zero active staleness flags before composite synthesis is permitted.


---

### LL-016 — A Review Command Must Start Its Own Comment
- **Identifier:** `LL-016`
- **Date:** 2026-10-26
- **Epic / Story:** Epic 36 / Story 36.3 (PR [#16](https://github.com/mdresch/agent-learning/pull/16))
- **Scope:** Universal Process
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 8.2); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** A triage comment that ended with the line `/q review` and a verdict request got no reply from the automated reviewer; a standalone comment that began with `/q` was answered within minutes. The wait on the first one cost about twenty minutes and one false conclusion that the reviewer was slow.
- **The Root Cause:** The reviewer reads a comment as a command only when `/q` opens it; a command inside a longer comment is plain text.
- **Actionable Invariant:** Post triage and the review command as two comments, and make the command the first characters of its comment. After posting, check that a reply or a new review appears on the new head commit before waiting longer.

---

### LL-017 — A Package-Root Re-Export Can Shadow an Existing Name
- **Identifier:** `LL-017`
- **Date:** 2026-10-26
- **Epic / Story:** Epic 36 / Story 36.5 (PR [#18](https://github.com/mdresch/agent-learning/pull/18))
- **Scope:** Universal Code Quality
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/methodology-catalog/SKILL.md` (section 8); Tier 3: `sidpa-template` conventions (proposed, needs human approval before any cross-repo change)
- **The Trap:** The new module's `to_episode_metadata`, named as the design specified, was added to the package's `__init__.py` imports. The root already exported a different function of the same name from another module, so the second import silently replaced the first; every caller of `agent_learning.to_episode_metadata` would have received the wrong function with no error.
- **The Root Cause:** A re-export is a plain name binding, and the import list was extended without searching for the name.
- **Actionable Invariant:** Before re-exporting a name from a package root, search the root for it. When it exists, keep the new function importable from its module and leave it out of the root, and say so in the module's skill and the test header.

---

### LL-018 — Name the Target Repository on Every PR Command
- **Identifier:** `LL-018`
- **Date:** 2026-10-26
- **Epic / Story:** Epic 36 / Story 36.3 (PR [#16](https://github.com/mdresch/agent-learning/pull/16))
- **Scope:** Universal Process
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 8.1); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** `gh pr create` for a pushed branch failed with "No commits between main and feat/story-36.3 ... Head sha can't be blank". The branch and its commits were on the remote. The skill already said to pass `--repo`; the command was run without it.
- **The Root Cause:** `gh` resolved the working directory's default repository to the upstream (`microsoft/agent-learning`), where the branch does not exist. The error describes the wrong repository's state, not a problem with the branch.
- **Actionable Invariant:** Pass `--repo` (or `-R`) on every `gh pr` and `gh api` command. When `gh` says a pushed branch has no commits, check `gh repo view` before touching the branch.

---

### LL-019 — Evidence Must Be Unambiguous in Its Own Representation
- **Identifier:** `LL-019`
- **Date:** 2026-10-26
- **Epic / Story:** Epic 36 / Story 36.3 (PR [#16](https://github.com/mdresch/agent-learning/pull/16))
- **Scope:** Universal Review
- **Tier 2/3 Propagation Target:** Tier 1 only
- **The Trap:** The reviewer twice claimed a regex used a doubled backslash. The claim was false, and the first rebuttal pasted Python's `repr` of the line, which shows a single backslash as two characters. The pasted evidence therefore appeared to support the false claim, and a correction comment was needed.
- **The Root Cause:** `repr` escapes backslashes, so its output cannot show how many are in the text. The rebuttal used a representation that hides the property in dispute.
- **Actionable Invariant:** When declining a finding about exact characters, show a measurement that does not depend on escaping: a count of the character, a hex dump, or the match result on a real input. Check that the evidence cannot be read the other way before posting it.


---

### LL-020 — Read a Mutable Global Once
- **Identifier:** `LL-020`
- **Date:** 2026-10-26
- **Epic / Story:** Epic 3 / Story 3.1 (PR [#11](https://github.com/mdresch/agent-learning/pull/11), commit `6a92064`)
- **Scope:** Universal Code Quality
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/autonomy/SKILL.md`; Tier 3: `sidpa-template` coding conventions (proposed, needs human approval before any cross-repo change)
- **The Trap:** `_note_global_override` read the global environment variable twice, once to test it and once to log it. A variable removed between the two reads raised `KeyError`. Automated review found it as a crash risk (Q-11-1).
- **The Root Cause:** A value that can change at any time was treated as stable across two statements.
- **Actionable Invariant:** Read an environment variable or other mutable global once into a local, and test and use the local. This applies to configuration, process state and files alike.

---

### LL-021 — Read a Posted Command Back Before Trusting a Reply
- **Identifier:** `LL-021`
- **Date:** 2026-10-26
- **Epic / Story:** Epic 3 / Story 3.1 (the review loop on PRs [#10](https://github.com/mdresch/agent-learning/pull/10) to [#12](https://github.com/mdresch/agent-learning/pull/12))
- **Scope:** Universal Process
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 8.2); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** On Windows Git Bash, `gh pr comment --body "/q review"` had its leading `/` rewritten into a path, so the reviewer never received the command. The replies that followed were its automatic reviews, and a polling script counted them as answers to the command.
- **The Root Cause:** The shell altered the argument on its way to the tool, and nothing checked what was actually posted or which commit a reply was for.
- **Actionable Invariant:** After posting a command to an external reviewer, read the posted text back, and accept a reply only when it is for the head commit the command named. Prefix such commands with `MSYS_NO_PATHCONV=1` or pass the body with `--body-file`.


---

### LL-022 — A Normative Pattern Must Be Run, Not Paraphrased
- **Identifier:** `LL-022`
- **Date:** 2026-10-27
- **Epic / Story:** Epic 12 / Story 12.3 (PR [#30](https://github.com/mdresch/agent-learning/pull/30))
- **Scope:** Universal Testing
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/plan-lint/SKILL.md` (done) and `.claude/skills/implement-story/SKILL.md` (Step 3); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** ADR-012 section 4.3.1 describes its word tokenizer in prose ("letters and digits, excluding underscore") and gives the pattern. A test written from the prose expected `snake_case` to count as two words. The pattern, run on that input, finds no token at all, because the underscore is a word character for `\b` and the whole word is skipped. The mismatch surfaced only because the test ran the real pattern.
- **The Root Cause:** The prose was read as the specification and the pattern as its illustration. When both are normative, they can disagree, and only running the pattern shows it.
- **Actionable Invariant:** Before writing a test from a spec that gives both prose and a pattern, run the pattern on every case the prose claims. Where they differ, pin the pattern's actual behavior in the test, report the gap to the maintainer, and change neither the code nor the ADR silently.

---

### LL-023 — Never Read a Document at Import Time in a Test File
- **Identifier:** `LL-023`
- **Date:** 2026-10-27
- **Epic / Story:** Epic 12 / Stories 12.1 and 12.3 (PRs [#28](https://github.com/mdresch/agent-learning/pull/28) and [#30](https://github.com/mdresch/agent-learning/pull/30); Q-28-1 and Q-30-1)
- **Scope:** Universal Testing
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 3); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** A test file looked up an ADR with `next(glob(...))` at module level. If the file is missing, import raises `StopIteration` and every test in the file is lost as one collection error. The same weakness came back in a new helper two stories later and was flagged again.
- **The Root Cause:** The lookup was written as a constant. A constant is evaluated at import, where a failure cannot be tied to the test that needed the file.
- **Actionable Invariant:** Read documents inside the helper or test that needs them, and assert that the file exists with a message naming the missing path. Do not default to `None` or skip: a silent skip hides drift between a spec and the code.

---

### LL-024 — Check What an Acceptance Criterion Leans On Before Scoring a Gate
- **Identifier:** `LL-024`
- **Date:** 2026-10-27
- **Epic / Story:** Epic 12 / Story 12.2 (approval gates, PR [#27](https://github.com/mdresch/agent-learning/pull/27))
- **Scope:** Universal Process
- **Tier 2/3 Propagation Target:** Tier 1 only
- **The Trap:** Story 12.2 AC_5 said the frontmatter of each daughter ADR would be "read from `docs/adr/`". The examples sit inside fenced blocks in the middle of those documents, not at the top, so a test had no stated way to find them. The gap was found only while checking the claims the story depends on, before scoring `approve-user-stories`.
- **The Root Cause:** An acceptance criterion named a source without saying how to extract from it, and the drafting step never ran the extraction.
- **Actionable Invariant:** Before scoring an approval gate, run or open each external artifact a criterion depends on, and fix the criterion so it states the extraction rule. A gate scores what it is shown; verify the claims behind it first.

---

### LL-025 — Shell Heredocs and Tool Inputs Change Backslashes
- **Identifier:** `LL-025`
- **Date:** 2026-10-27
- **Epic / Story:** Epic 12 / Story 12.3 (PR [#30](https://github.com/mdresch/agent-learning/pull/30))
- **Scope:** Universal Tooling
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 5); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** A tokenizer pattern was appended through a shell heredoc. Its `\b` markers arrived as backspace characters, so the pattern silently lost both word boundaries. A tool parameter likewise turned a `\u2019` escape into the character itself. Nothing failed at write time; the test comparing the pattern caught it.
- **The Root Cause:** The text passed through a layer that interprets escape sequences before the file received it.
- **Actionable Invariant:** Write code that contains backslashes or escape sequences with the file-write tool, not a shell heredoc, and read the result back with a measurement that does not depend on escaping (see LL-019): the pattern's `.pattern` value, a character count, or a match on a real input.

---

### LL-026 — Do Not Run an Auto-Fixer on Files Outside Your Change
- **Identifier:** `LL-026`
- **Date:** 2026-10-27
- **Epic / Story:** Epic 12 / Story 12.4 (PR [#32](https://github.com/mdresch/agent-learning/pull/32))
- **Scope:** Universal Tooling
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 6); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** `ruff check --fix` was run on `src/agent_learning/__init__.py` after adding three exports. The file had an import block that was already out of order, and the fixer re-sorted all of it: 251 changed lines in a story that needed 6.
- **The Root Cause:** The fixer repairs every violation in a file, not only the ones the change introduced.
- **Actionable Invariant:** Run `ruff check --fix` only on files the change created. For an existing file, run `ruff check` without `--fix` and fix new findings by hand. Read `git diff --stat` before committing; a small change with a large diff is a signal to revert and redo it.

---

### LL-027 — Approvals Must Be Committed Before the Code They Gate
- **Identifier:** `LL-027`
- **Date:** 2026-10-28
- **Epic / Story:** Epic 13 / Stories 13.1–13.7 (PR [#42](https://github.com/mdresch/agent-learning/pull/42))
- **Scope:** Universal Process
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 0); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** The BRD, FDD and Epic 13 were approved through `approve-brd/fdd/user-stories`, but the episodes and decision records stayed uncommitted in the working tree while the code was built. The history showed code with no approval behind it.
- **The Root Cause:** An approval is a file in the working tree until it is committed; nothing in the loop checks that it reached a commit.
- **Actionable Invariant:** Commit the approval records (`docs/policy-shapes/...`) in a docs commit before the first code commit of the story, and have the PR show them. At Step 0, confirm with `git log` that the approval is in history.

---

### LL-028 — An Unloaded Skill Is Not Followed
- **Identifier:** `LL-028`
- **Date:** 2026-10-28
- **Epic / Story:** Epic 13 / Stories 13.1–13.7 (PR [#42](https://github.com/mdresch/agent-learning/pull/42))
- **Scope:** Universal Process
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 0, load the skill and re-read it before each step); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** Seven stories were built in one working tree and committed together in `d9c8bdb`, with no worktree or PR per story and no RED run before the code. The loop was applied from memory, not from the skill text.
- **The Root Cause:** The skill steps were remembered, not read; a remembered loop drops the steps that feel like overhead.
- **Actionable Invariant:** Invoke the skill at the start of the story and re-read the step before doing it. Where a step was missed and cannot be recovered, record the deviation in the log; do not claim a result (such as "observed RED first") that did not happen.

---

### LL-029 — Do Not Use Python `hash()` in Tests
- **Identifier:** `LL-029`
- **Date:** 2026-10-28
- **Epic / Story:** Epic 13 / Stories 13.1–13.7 (PR [#42](https://github.com/mdresch/agent-learning/pull/42))
- **Scope:** Universal Testing
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 3, test rules); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** The Story 13.5 test derived plan hashes with `hash()`. It passed locally, but `hash()` of a `str` is salted per process, so the values change on every run and the test depends on chance.
- **The Root Cause:** The built-in `hash()` is made for dict lookup, not for stable values.
- **Actionable Invariant:** In tests, derive any stable digest with `hashlib.sha256`. Treat `hash(` in a test file as a finding.

---

### LL-030 — A Missing Tool Is Not a Skipped Gate
- **Identifier:** `LL-030`
- **Date:** 2026-10-28
- **Epic / Story:** Epic 13 / Stories 13.1–13.7 (PR [#42](https://github.com/mdresch/agent-learning/pull/42))
- **Scope:** Universal Tooling
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 6); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** `ruff` was reported as not installed and the lint gate was skipped. Amazon Q then named the gap, `uvx ruff` ran at once, and it found 29 findings in the new files.
- **The Root Cause:** "Not installed" was read as "cannot run". `uvx` runs a tool without installing it.
- **Actionable Invariant:** When a gate's tool is missing, try `uvx <tool>` (or the project's runner) before skipping. Skip only if that fails, and then record the gate as not run, with the reason.

---

### LL-031 — Triage a Reviewer's Confirmation Too
- **Identifier:** `LL-031`
- **Date:** 2026-10-28
- **Epic / Story:** Epic 13 / Stories 13.1–13.7 (PR [#42](https://github.com/mdresch/agent-learning/pull/42))
- **Scope:** Universal Process
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 8); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** After the fixes, Amazon Q's confirmation at head `21285eb` still contained a stale claim about ruff and a noise item (`Q-28-1`) that belonged to an older PR. Taking the confirmation at face value would have recorded both as findings.
- **The Root Cause:** Q's confirmations rest on logs and can repeat what is already resolved or belongs elsewhere.
- **Actionable Invariant:** Check each claim in a confirmation against the head commit, as with a first-round finding. Log the ones that are stale or out of scope as noise with the reason.

---

### LL-032 — Check for an Omission Without a Filter
- **Identifier:** `LL-032`
- **Date:** 2026-10-28
- **Epic / Story:** Epic 13 / Stories 13.1–13.7 (PR [#42](https://github.com/mdresch/agent-learning/pull/42))
- **Scope:** Universal Process
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/implement-story/SKILL.md` (Step 9, audit); Tier 3: `sidpa-template` implement-story skill (proposed, needs human approval before any cross-repo change)
- **The Trap:** An audit said the log omitted acceptance criteria. The check had been run through a filter that hid them, so the claim was wrong and had to be retracted.
- **The Root Cause:** A filtered view cannot prove that something is absent.
- **Actionable Invariant:** To claim an omission, read the unfiltered source (for example `grep -c` on the whole entry, or the file itself) and quote what you saw. A filtered output only supports "not found in this view".
