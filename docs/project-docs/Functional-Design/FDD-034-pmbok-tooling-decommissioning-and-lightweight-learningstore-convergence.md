# FDD-034: PMBOK Tooling Decommissioning and Lightweight LearningStore Convergence

**Source ADR:** [ADR-034](../../adr/ADR-034-pmbok-tooling-decommissioning-and-lightweight-learningstore-convergence.md) — Accepted (2026-10-26)  
**Source BRD:** [BRD-034](../Business-Requirements/BRD-034-pmbok-tooling-decommissioning-and-lightweight-learningstore-convergence.md)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-034 and BRD-034; adjudicated via `approve-fdd` (robust utility 0.736, episode `1b234e07-d329-4d7e-8df2-ed460511aee1`). §5 item 3 is confirmed for Story 34.3 (2026-10-31); item 4 remains unconfirmed.

---

## 1. Architecture and Component Placement

1. **Already delivered.** Epic 12 owns `parser.py` and the plan lint. Epic 13 owns `hashing.py`, `integrity.py`, `governance.py`, and formalization. This design does not change their contracts. ADR-034 §4.2.2 remains the illustrative sketch those epics specified.
2. **Registry** lives in `src/agent_learning/pmbok/legacy_registry.py`. It is data. It does not import `pmbok`, `LearningStore`, or `pydantic`.
3. **Run ordering** lives in `src/agent_learning/pmbok/run_state.py`. It takes plain records and returns the latest one. It does not import the store.
4. **Runtime** lives in `src/agent_learning/pmbok_runtime/`. `runs.py` reads and appends episodes through a store the caller passes. `client.py` performs HTTP and sleep. `orchestrator.py` calls the pure Epic 13 functions and the registry. `src/agent_learning/cli.py` only parses arguments and calls the runtime.
5. **Purity line.** `agent_learning.pmbok` gains no network, no sleep, and no store import. `pmbok_runtime` may import `LearningStore` and may sleep inside `client.py`.

---

## 2. Data Contract

```python
# legacy_registry.py — frozen copy of pmbok/process_registry.py PROCESS_DEPENDENCY_MAP
LEGACY_PROCESSES: Mapping[str, tuple[str, ...]]  # process_id -> prerequisite ids, sorted as in the legacy map

RUN_AGENT_ID = "pmbok-orchestration"
RUN_TASK_ID = "pmbok-lifecycle-run"
PROCESS_STATUSES = ("not_started", "in_progress", "completed", "failed")

@dataclass(frozen=True)
class RunSnapshot:
    run_id: str
    sequence_number: int
    created_at: str
    phase: str
    processes: Mapping[str, str]          # process_id -> one of PROCESS_STATUSES
    baseline_hash: str | None
    gate_episode_ids: Mapping[str, tuple[str, str, str]]   # plan_id -> (episode_id, canonical_hash, verdict)
    route_episode_ids: Mapping[str, str]  # plan_id -> route episode_id

@dataclass(frozen=True)
class RunEpisodeFields:
    agent_id: str            # RUN_AGENT_ID
    task_id: str             # RUN_TASK_ID
    action_type: str         # "governance"
    action_logprob: None
    metadata: Mapping[str, object]
    result_summary: str
```

The forty-nine process ids are `4.1`–`4.7`, `5.1`–`5.6`, `6.1`–`6.6`, `7.1`–`7.4`, `8.1`–`8.3`, `9.1`–`9.6`, `10.1`–`10.3`, `11.1`–`11.7`, `12.1`–`12.3`, and `13.1`–`13.4`. Prerequisite lists match the legacy map, including `5.1 -> (4.1,)` and `4.2` depending on `4.1`, `5.1`, `6.1`, `7.1`, `8.1`, `9.1`, `10.1`, `11.1`, `12.1`, and `13.2`.

`metadata` keys for a run are `run_id`, `phase`, `processes`, `sequence_number`, `baseline_hash`, `gate_episode_ids`, and `route_episode_ids`. No other key is added. A string value longer than 256 characters is refused, the same ceiling Story 13.3 uses. `result_summary` uses that same ceiling. The runtime `append_run` adapter returns an Episode whose id matches the id returned by `LearningStore.store_episode`.

```python
# client.py
def backoff_delays(attempts: int, base_seconds: float, factor: float, jitter: Callable[[], float]) -> list[float]: ...

class LlmClient(Protocol):
    def complete(self, prompt: str) -> str: ...

def urllib_client(
    url: str,
    sleeper: Callable[[float], None],
    delays: Sequence[float],
    *,
    credential_env_var: str | None = None,
) -> LlmClient: ...
def mock_client(body: str) -> LlmClient: ...
```

`attempts`, `base_seconds`, and `factor` are arguments. This design sets no hidden default. Jitter is additive seconds: `backoff_delays` calls the supplied jitter function once per delay and adds its return value to `base_seconds * factor**index`. Menno confirmed this parameterized interpretation for Story 34.3 on 2026-10-31. The client sends the prompt as UTF-8 request data and returns the UTF-8 response body. When `credential_env_var` is supplied, `urllib_client.complete` reads that environment variable at call time and sends its value as a Bearer `Authorization` header; if the named variable is unset, it raises `ValueError` without revealing the variable's value. `mock_client` returns `body` and does not call the sleeper.

---

## 3. Behavior

### 3.1 `legacy_processes() -> Mapping[str, tuple[str, ...]]` (BRU-034-04)

Returns the frozen map. A caller cannot mutate it. Looking up an id that is not one of the forty-nine raises `KeyError`. Every `PlanStandard.legacy` value in `PLAN_STANDARDS` is a key.

### 3.2 `latest_run(snapshots) -> RunSnapshot | None` (BRU-034-02)

Returns `None` for an empty sequence. Otherwise returns the snapshot with the greatest `(sequence_number, created_at)`. `created_at` must be a timezone-aware ISO-8601 timestamp; comparisons normalize it to UTC while preserving the original string in stored data. The input sequence is not reordered. Ties on sequence and normalized timestamp keep the earlier input item.

### 3.3 `build_run_fields(snapshot, result_summary) -> RunEpisodeFields` (BRU-034-02, BRU-034-06, BRU-034-08)

Fills the identity fields in §2. `action_logprob` is `None`. `metadata` is the seven keys in §2 and nothing else. `run_id` is a non-empty UUID string. An empty `run_id`, a negative `sequence_number`, an unknown process id, an unknown status, or a string above 256 characters raises `ValueError` naming the field. The function does not write a store.

`latest_run_for` applies this validation to each matching persisted Episode after validating its stored field shapes. The process registry and status set are frozen by this FDD; a persisted run with an unknown process id or status is malformed and raises an error naming the Episode id. Historical Episodes remain readable across changes to unrelated runtime code, not across changes to this frozen contract.

### 3.4 Client (BRU-034-01, BRU-034-04, BRU-034-06)

`urllib_client.complete` sends the UTF-8 prompt with `urllib.request` and returns the UTF-8 response body. On a failure that is an `URLError` or an HTTP status of 429 or 500 through 599, it sleeps the next delay and tries again, until the delays are exhausted, then raises the last error. Any other status raises immediately. The `Authorization` header, when the caller supplies a credential environment-variable name, is read from that variable at call time (`AZURE_OPENAI_KEY` or `OPENAI_API_KEY`) and sent as a Bearer token. An unset named variable raises `ValueError`; the header value is not included in exception text or logs. `mock_client.complete` returns the canned body, sleeps zero times, and opens no socket.

### 3.5 Commands (BRU-034-05)

`agent-learn pmbok --help` exits 0 and lists `draft`, `approve`, `formalize`, and `adapt`.

- `draft --charter <path> [--plan <id>] [--mock]` with `--mock` asks `mock_client` for a body and does not open a socket. Without `--mock` it uses `urllib_client`. The generated file is written by the runtime, not by `agent_learning.pmbok`.
- `approve --plan <id>` builds one `approve-subsidiary-plan` episode through the Epic 13 producer. `approve --all --interactive` iterates `full_plan` routes only, in `DRAFT_ORDER`. A plan whose lint findings are empty may have an empty rationale. A plan with one or more findings and a blank or whitespace rationale is skipped, and no episode is written for it. Each accepted plan is one episode. The rationale is `result_summary` and is not an eighth metadata key.
- `formalize --baseline-id <id>` runs the Epic 13 formalization check. When it is ready, the command prints `agent-learn task-policy-decide --agent-id agent-learning-governance --task-id approve-pmp` and does not execute it. When it is not ready, it prints the blockers and exits non-zero.
- `adapt --adaptation-plan <path>` records one run episode whose `phase` is `adaptation`. It does not approve the adaptation plan.

There is no `--mode full` flag.

### 3.6 Decommission (BRU-034-03, BRU-034-07)

In Story 34.5, delete `pmbok/`, `scripts/orchestrate_pmbok.py`, and `tests/pmbok/`. Remove `--ignore=tests/pmbok` from `.github/workflows/tests.yaml` and from `scripts/build_linux_installer.sh`. `pyproject.toml` does not list `sqlalchemy`, `fastapi`, `typer`, `tenacity`, `pytesseract`, `pdf2image`, `pillow`, or `pyyaml`. ERR-034-05 is satisfied by deleting `pmbok/audit/policy_loader.py` with the tree. No YAML file is converted. Until then, the CI workflow explicitly excludes `tests/pmbok/`; the exclusion is removed by Story 34.5.

---

## 4. Error Handling

| Situation | Behavior |
|---|---|
| Unknown process id or status | `ValueError` naming the field |
| Empty `run_id`, negative `sequence_number`, invalid `created_at`, or a string over 256 characters | `ValueError` naming the field |
| Non-string `run_id` | `ValueError` naming the field |
| Non-string `created_at` | `TypeError` naming the field |
| Boolean `sequence_number` | `TypeError` naming the field; booleans are not sequence integers |
| Non-string `phase` | `TypeError` naming the field |
| `latest_run_for` observes zero Episodes | Return `None`; the read is linearized at the count observation |
| Episode count changes during `latest_run_for` | Compare the task-wide count before and after the query. Because run Episodes are append-only, a write between those calls changes the count and invalidates the read; retry up to three read attempts, then raise `RuntimeError` rather than return a potentially stale snapshot |
| Stored Episode has invalid `created_at` | Raise `TypeError` or `ValueError` naming the Episode id and `created_at` |
| `latest_run` receives an invalid timestamp | Raise `TypeError` or `ValueError` naming `created_at` |
| Same `(sequence_number, created_at)` twice | The earlier input snapshot is kept |
| HTTP 429 or 500–599, delays remaining | Sleep the next delay and retry |
| Any other HTTP status | Raise immediately, with no credential in the message |
| Flagged plan, blank rationale | That plan is skipped; other plans in the batch still proceed |
| Formalization blockers | Exit non-zero and print each blocker; do not print the `approve-pmp` command |
| `mock` client | No sleep and no socket |

---

## 5. Interpretations to Confirm

These are not verbatim in ADR-034. Story 34.3's item 3 is confirmed; Story 34.4 still waits on item 4.

1. **Epic 34 starts where Epics 12 and 13 stop.** The parser, hash, integrity, graph, freshness, lifecycle, and formalization functions are called, not rewritten. ADR-034's "Epic 12" labels are Epic 34.
2. **The registry is the legacy map, frozen.** Forty-nine ids, prerequisite lists copied from `PROCESS_DEPENDENCY_MAP`, without the legacy pydantic models.
3. **Backoff numbers are arguments (confirmed for Story 34.3 by Menno, 2026-10-31).** The ADR names exponential backoff and jitter and sets no base, factor, or attempt count. Tests pass those values and a fake sleeper. The confirmed jitter interpretation is additive seconds, called once per delay and added to the exponential delay.
4. **A batch rationale is `result_summary`, capped at 256 characters.** It is not a new key on the Epic 13 approval metadata. A flagged plan with a blank rationale is skipped. An unflagged plan may omit it. The batch listing is text on stdout. There is no web UI.
5. **`formalize` does not run `approve-pmp`.** It prints the command when the Epic 13 check is ready.
6. **Deleting `policy_loader.py` closes ERR-034-05.** Files that are deleted are not converted to JSON.
7. **Learner exclusion stays Story 1.1.** This epic sets `action_type` and `action_logprob` and does not change the trainer.
8. **Spark stays ignored.** Only the `tests/pmbok` ignore is removed.
9. **Latest-run read retries are bounded and task-scoped.** `latest_run_for` returns `None` at a zero-count observation; otherwise it makes at most three attempts to observe a stable append-only count for the orchestration task. Any concurrent write for that task may invalidate the read, even if it belongs to another run; after three unstable attempts it raises `RuntimeError` rather than return a potentially stale snapshot.
10. **Run timestamps are offset-aware (confirmed for Story 34.2).** `created_at` accepts timezone-aware ISO-8601 values; ordering compares the represented instants in UTC and stores the original string.

## 6. Out of Scope

Same boundary as BRD-034. `legacy_registry.py` and `run_state.py` do not import the store. The runtime does not create a SQLite file and does not add a `LearningStore` record type.
