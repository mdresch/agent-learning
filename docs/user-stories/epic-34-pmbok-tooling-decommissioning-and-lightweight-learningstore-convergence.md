# Epic 34: PMBOK Tooling Decommissioning and Lightweight LearningStore Convergence

**Source ADR:** [ADR-034](../adr/ADR-034-pmbok-tooling-decommissioning-and-lightweight-learningstore-convergence.md) — Accepted (2026-10-26)  
**Source BRD/FDD:** [BRD-034](../project-docs/Business-Requirements/BRD-034-pmbok-tooling-decommissioning-and-lightweight-learningstore-convergence.md) / [FDD-034](../project-docs/Functional-Design/FDD-034-pmbok-tooling-decommissioning-and-lightweight-learningstore-convergence.md)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-034, BRD-034 and FDD-034 (Approved 2026-10-30); adjudicated via `approve-user-stories` (robust utility 0.726, episode `dd78f67b-d1d1-47da-8867-1d07e4e43132`).

Five stories. Each rule sits in one story (LL-012). Contract tests: `tests/test_legacy_registry.py` (34.1), `tests/test_pmbok_run_state.py` (34.2), `tests/test_pmbok_client.py` (34.3), `tests/test_pmbok_cli.py` (34.4), `tests/test_pmbok_decommission.py` (34.5). Stories 34.3 and 34.4 wait until FDD-034 §5 items 3 and 4 are confirmed. BRU-034-08 has no story of its own: Story 34.2 sets the two fields Story 1.1 already filters on.

ADR-034 §6 says "Epic 12". That label means this epic. Epics 12 and 13 stay as they are.

---

## Story 34.1 — The 49-process registry is pure data

**Status:** Draft  
**As** a maintainer,  
**I want** the legacy process codes and their prerequisites available without the legacy package,  
**so that** a plan's `legacy_process` still names a real code after `pmbok/` is deleted.

### Acceptance Criteria

- **$AC_0$ (Catalogue):** `legacy_processes()` has exactly the forty-nine ids in FDD-034 §2. `5.1` depends on `4.1`. `4.2` depends on `4.1`, `5.1`, `6.1`, `7.1`, `8.1`, `9.1`, `10.1`, `11.1`, `12.1`, and `13.2`. An unknown id raises `KeyError`.
- **$AC_1$ (Plan codes):** Every `legacy` value on `PLAN_STANDARDS` is a key.
- **$AC_2$ (Frozen):** Replacing a value in the returned mapping raises. A second call returns equal data.
- **$AC_3$ (Purity):** `legacy_registry.py` imports neither `LearningStore`, `pydantic`, nor the top-level `pmbok` package. Importing it does not read a file and does not open a socket.

---

## Story 34.2 — A project run is an Episode, and the latest one wins

**Status:** Draft  
**As** a governance reviewer,  
**I want** each orchestration run stored as one more Episode, with the newest sequence winning,  
**so that** project state lives in `LearningStore` and a later event does not rewrite an earlier one.

### Acceptance Criteria

- **$AC_0$ (Identity):** `build_run_fields` sets `agent_id` `pmbok-orchestration`, `task_id` `pmbok-lifecycle-run`, `action_type` `governance`, and `action_logprob` `None`. `metadata` has exactly `run_id`, `phase`, `processes`, `sequence_number`, `baseline_hash`, `gate_episode_ids`, and `route_episode_ids`.
- **$AC_1$ (Latest):** `latest_run` of an empty sequence is `None`. Of two snapshots, the one with the greater `(sequence_number, created_at)` is returned. The input order is unchanged. Equal keys keep the earlier item.
- **$AC_2$ (Refusals):** An empty `run_id`, a negative `sequence_number`, an unknown process id, an unknown status, or any string longer than 256 characters raises `ValueError` naming the field.
- **$AC_3$ (No store write):** `build_run_fields` and `latest_run` do not call a store. `run_state.py` imports no storage module.
- **$AC_4$ (No database):** A test double of the runtime append path writes an Episode and creates no `*.db` file.

---

## Story 34.3 — The client is the standard library, and secrets stay out of the record

**Status:** Draft — blocked on confirmation of FDD-034 §5 item 3  
**As** a maintainer,  
**I want** live calls to use `urllib` and an explicit backoff, and the offline client to touch neither the network nor a credential,  
**so that** `tenacity` is unnecessary and a key cannot land in an episode or a log.

### Acceptance Criteria

- **$AC_0$ (Delays):** `backoff_delays(3, 0.5, 2.0, jitter)` returns three delays. With a jitter of zero they are `0.5`, `1.0`, and `2.0`. The function sleeps zero times.
- **$AC_1$ (Retry):** A fake HTTP stack that returns 429 and then 200 causes one sleep of the next delay and one successful body. A status of 400 raises on the first try, with no sleep. A status of 500 followed by an exhausted delay list raises the last error.
- **$AC_2$ (Secret):** The credential string passed as the environment value is absent from the exception text and from every `RunEpisodeFields` built in the same test.
- **$AC_3$ (Mock):** `mock_client("hello").complete("prompt")` returns `hello`, records zero sleeps, and the test's socket factory is not called.
- **$AC_4$ (Boundary):** `client.py` imports neither `tenacity` nor `LearningStore`. `agent_learning.pmbok` still imports no `client.py`.

---

## Story 34.4 — One CLI dispatches draft, approve, formalize, and adapt

**Status:** Draft — blocked on confirmation of FDD-034 §5 items 3 and 4, and on Stories 34.2 and 34.3  
**As** a maintainer,  
**I want** PMBOK commands on `agent-learn` only, each plan still getting its own episode,  
**so that** a batch review cannot collapse several approvals into one record.

### Acceptance Criteria

- **$AC_0$ (Help):** `agent-learn pmbok --help` exits 0. Its stdout names `draft`, `approve`, `formalize`, and `adapt`. `--mode full` is rejected as an unknown argument.
- **$AC_1$ (Mock draft):** `draft --charter <path> --mock` asks the mock client and does not call the socket factory.
- **$AC_2$ (Batch):** Two `full_plan` routes and one `pmp_section` route write two episodes, in `DRAFT_ORDER`, and none for the section. A `full_plan` with a lint finding and a blank rationale writes no episode. The same plan with rationale `because the floor is waived` writes one episode whose `result_summary` is that text. A rationale of 257 characters raises `ValueError` and writes nothing for that plan.
- **$AC_3$ (Formalize):** When the Epic 13 check is ready, stdout contains `task-policy-decide` and `approve-pmp`, and that command is not executed. When the check returns a blocker, the exit code is non-zero, the blocker plan id is printed, and `approve-pmp` is absent from stdout.
- **$AC_4$ (Single entry):** `pmbok/cli/main.py` is not invoked. The new subparser is registered from `src/agent_learning/cli.py`.

---

## Story 34.5 — The legacy tree is gone and the suite collects

**Status:** Draft — blocked on Stories 34.1, 34.2, 34.3, and 34.4  
**As** a maintainer,  
**I want** the unused SQLite, FastAPI, and Typer tree deleted, and `pytest` able to collect what remains,  
**so that** a clean run no longer needs `--ignore=tests/pmbok`.

### Acceptance Criteria

- **$AC_0$ (Deleted):** `pmbok/` and `scripts/orchestrate_pmbok.py` and `tests/pmbok/` are absent. A repository search finds no import of the top-level package `pmbok`.
- **$AC_1$ (Ignore flag):** `.github/workflows/tests.yaml` and `scripts/build_linux_installer.sh` contain no `--ignore=tests/pmbok`.
- **$AC_2$ (Dependencies):** `pyproject.toml` names none of `sqlalchemy`, `fastapi`, `typer`, `tenacity`, `pytesseract`, `pdf2image`, `pillow`, and `pyyaml`.
- **$AC_3$ (Collection):** `pytest --collect-only -q` completes without a collection error from a missing `tests/pmbok` module. `tests/test_spark.py` may still be ignored.
- **$AC_4$ (Help still works):** `agent-learn pmbok --help` exits 0 after the deletion.

---

## Out of Scope for this epic

- Changing the Epic 12 parser or the Epic 13 hash, integrity, graph, freshness, lifecycle, or formalization contracts.
- Implementing `approve-pmp`.
- Adding an eighth key to the Epic 13 approval metadata.
- Porting the model to forty PMBOK 8 processes.
- Copying legacy SQLite rows.
- Changing the Story 1.1 trainer filter.
- Collecting `tests/test_spark.py` without a JVM.
