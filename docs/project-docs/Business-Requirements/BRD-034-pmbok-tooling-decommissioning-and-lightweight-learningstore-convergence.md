# BRD-034: PMBOK Tooling Decommissioning and Lightweight LearningStore Convergence

**Source ADR:** [ADR-034](../../adr/ADR-034-pmbok-tooling-decommissioning-and-lightweight-learningstore-convergence.md) — Accepted (2026-10-26, Menno); Episode `3512706e-d5ea-4f5c-9c54-642653fd5fcf`  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Proposed)  
**Status:** Draft (2026-10-29) — derived from Accepted ADR-034; not yet adjudicated via `approve-brd`.  
**Stakeholders:** Menno (Sponsor, Project Manager, maintainer)

## Business Need

The legacy top-level `pmbok/` tree is a second stack beside `agent-learning`. It opens SQLite through SQLAlchemy, ships an unused FastAPI server and a Typer CLI, and imports packages that `pyproject.toml` does not declare. A clean `pytest` cannot collect `tests/pmbok`, so runners pass `--ignore=tests/pmbok` (LL-013). ADR-002 already says project state is an `Episode` in `LearningStore`. ADR-008 §4.2, the part this ADR amends, pointed at that legacy tree.

Epics 12 and 13 already delivered the pure plan parser, the content hash, technical integrity, the dependency graph, freshness, lifecycle projection, and formalization readiness. This requirement covers what those epics left: the 49-process registry as plain data, a project run recorded as an `Episode`, a standard-library client, one `agent-learn pmbok` command surface, and the deletion of the legacy tree so the suite collects without ignoring it. ADR-034 §6 calls this work Epic 12. The 2026-10-27 correction says to read that as Epic 34.

## Business Rules (BRU)

- **BRU-034-01 (No new heavyweight runtime dependency):** `pyproject.toml` does not gain `sqlalchemy`, `fastapi`, `typer`, `tenacity`, `pytesseract`, `pdf2image`, `pillow`, or `pyyaml`. A runtime dependency outside the existing lightweight baseline needs its own ADR (ADR-034 Invariant 1). The allowed baseline stays `numpy`, `pydantic`, `azure-identity`, and the optional `azure-cosmos` extra.
- **BRU-034-02 (A project run is an Episode):** Process state, gate cross-references, and the active baseline hash are fields on an `Episode` with `agent_id` `pmbok-orchestration`, `task_id` `pmbok-lifecycle-run`, `action_type` `governance`, and `action_logprob` `None`. The current run is the latest episode for that `run_id`, ordered by `sequence_number` then `created_at`. No supported command creates or opens a `*.db` file (ADR-034 Invariant 2). Existing SQLite files are discarded. No rows are copied out of them.
- **BRU-034-03 (The suite collects):** `pytest` and the CI test command do not pass `--ignore=tests/pmbok`. A missing optional extra skips. It does not fail collection (ADR-034 Invariant 3). `tests/test_spark.py` may still be ignored where a JVM is absent. That ignore is not this requirement.
- **BRU-034-04 (The domain package stays pure):** `agent_learning.pmbok` imports neither `LearningStore` nor the legacy `pmbok` package, and it performs no network I/O and no sleep. The 49 legacy process codes and their prerequisite lists live there as data. Store queries, HTTP, and retry sleep live in `agent_learning.pmbok_runtime` (ADR-034 Invariant 4).
- **BRU-034-05 (One command surface):** The only CLI entry point is `agent-learn` in `src/agent_learning/cli.py`. PMBOK commands are `agent-learn pmbok draft`, `approve`, `formalize`, and `adapt` (ADR-034 Invariant 5). `approve --all --interactive` considers `full_plan` routes only and writes one gate episode per plan. A flagged plan needs its own non-empty rationale. `formalize` surfaces the existing `approve-pmp` invocation. It does not implement that policy. `--mode full` is not ported.
- **BRU-034-06 (The record stays small):** Run metadata holds identifiers, hashes, route strings, process-status codes, and relative paths. It does not hold plan markdown, Charter prose, or a credential. `AZURE_OPENAI_KEY` and `OPENAI_API_KEY` are read from the environment at the moment of a live call and are not written to an episode or a log line (ADR-034 Invariant 6).
- **BRU-034-07 (The legacy tree is deleted after the port):** When the registry, the run episode, the client, and the commands exist, `pmbok/`, `scripts/orchestrate_pmbok.py`, and the tests that import them are deleted. Nothing in the repository imports the top-level `pmbok` package. `agent-learn pmbok --help` exits successfully.
- **BRU-034-08 (Orchestration episodes are not training rows):** A `pmbok-lifecycle-run` episode carries `action_type` `governance` and `action_logprob` `None`, which is the mark Story 1.1 already uses to keep a row out of REINFORCE. This requirement does not add a second filter.

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Registry | The pure catalogue has the 49 legacy process ids, and each of the nine plan `legacy_process` codes is one of them |
| Purity | 0 imports of `LearningStore` or the legacy `pmbok` package from `agent_learning.pmbok` |
| Run record | A second episode with a higher sequence number becomes the current run; the first episode is unchanged |
| Secrets | 0 episode fields and 0 log lines that contain a credential value |
| Client | The mock client opens no socket and calls no sleep |
| CLI | `agent-learn pmbok --help` exits 0 and names `draft`, `approve`, `formalize`, and `adapt` |
| Batch | A batch of two full plans writes two episodes; a flagged plan with a blank rationale writes none |
| Collection | 0 `--ignore=tests/pmbok` flags in the CI test command or the Linux installer script |
| Decommission | 0 files under `pmbok/` and 0 copies of `scripts/orchestrate_pmbok.py` after the port |
| Storage | 0 new `LearningStore` record types; 0 `*.db` files created by a supported command |

## Out of Scope

- The frontmatter parser, content lint, canonical hash, technical integrity, `PLAN_DAG`, freshness, lifecycle projection, and formalization readiness (Epics 12 and 13). ADR-034 Tests 1 through 6 are already mapped there, except the registry port.
- Building the `approve-pmp` policy. This epic only surfaces its existing command after formalize.
- The `approve-subsidiary-plan` action shape (Story 13.3, ERR-034-02).
- A PMBOK 8 forty-process model. The bridge stays the 49 sixth-edition codes.
- OCR, a web server, and a second CLI framework.
- Copying rows out of `data/pmbok_runtime/*.db`.
- Rewriting Story 1.1's learner filter.
- The route-approval locus convention (ERR-034-04). It has no code in this epic.
- `tests/test_spark.py` and its JVM.
