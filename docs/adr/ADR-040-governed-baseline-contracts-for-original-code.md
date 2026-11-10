# ADR 040: Governed Baseline Contracts for the Original SDK Code

## 1. Executive Brief
The `agent-learning` SDK came from `microsoft/agent-learning`. Its 54 source files have Microsoft's own tests, but no story, ADR, BRD or FDD stands behind those tests, and most of the files are named by no component skill. This fork has added governed work (Epics 7 to 38) on top. This ADR decides how the original code gets the same contract layer: characterization contracts that pin what the code does today, written through `implement-story`, starting with the eight original files that the full suite covers least. It does not change production code, and it does not claim the original code was designed under this governance.

## 2. Status
**Accepted (2026-11-10, Menno)** — approval episode `69365299` (`approve-adr`, robust utility 0.760, expected utility 0.827, against 0.044 for reject and 0.119 for request-revision), recorded on 2026-11-04 as a catch-up approval and confirmed by the maintainer on 2026-11-10. The recorded score was produced by the ADR's author (`author_scored_own_adr`). Nothing in this ADR is built. This is catch-up work and is recorded as catch-up. Numbered ADR-039 until 2026-11-09 (see the Amendment Log).

## 3. Context & Problem Statement
- **Governed cover is missing on original code.** Of the 26 test files Microsoft ships, three carry any Story or ADR header, and this fork added those headers. The rest are plain tests. `docs/project-docs/Pillar-Code-Map.md` (Draft, PR #116) records the mapping of each original file to a pillar and its coverage.
- **Eight original files are poorly covered even by the full suite** (line coverage, 2026-11-04, `pytest --ignore=tests/test_spark.py --ignore=tests/pmbok`):

| File | Statements | Coverage | Pillar |
|---|---|---|---|
| `classifiers/router.py` | 120 | 26% | Frozen-model, in-process learning |
| `metrics/intent_resolution.py` | 22 | 45% | Frozen-model, in-process learning |
| `metrics/task_completion.py` | 22 | 45% | Frozen-model, in-process learning |
| `spark.py` | 48 | 46% | Frozen-model, in-process learning |
| `storage/cosmos.py` | 288 | 46% | Frozen-model, in-process learning |
| `metrics/base.py` | 89 | 51% | Frozen-model, in-process learning |
| `metrics/task_adherence.py` | 18 | 56% | Frozen-model, in-process learning |
| `classifiers/base.py` | 88 | 57% | Frozen-model, in-process learning |

  `spark.py`'s figure is low partly because its test file needs a JVM and is excluded here. `cli.py` was 54% from Microsoft's tests alone but is 88% with this fork's tests, so it is not in this set.
- **A coverage number is an observation, not a contract.** A line can be executed by a test that asserts nothing. The contract layer this repository uses is one test per acceptance criterion, with the governing Story and ADR named in its header.
- **The original code was not designed under this governance.** Writing an ADR that says otherwise would invent history. The honest form is a characterization: record what the code does, mark any gap between its docstring and its behavior as a finding, and do not fix it silently.

## 4. Decision

### 4.1 Characterization contracts, not redesign
Each original file in scope gets contracts that pin its behavior as observed on 2026-11-04. A contract that disagrees with a docstring is recorded as a finding and goes through `heal-contract-failure`. The test is not bent to the code, and the code is not changed to satisfy a guess.

### 4.2 Four work groups
- **G1 Classifiers** (`classifiers/base.py`, `classifiers/router.py`): logistic and softmax primitives, `fit` and `fit_from_catalog`, the `refused` path below `refusal_threshold`, feature-dimension errors, and the snapshot round trip.
- **G2 Metrics** (`metrics/base.py`, `task_completion.py`, `task_adherence.py`, `intent_resolution.py`): request building from an `Episode`, the empty-input and evaluator-error `skipped` paths, normalization to `[0, 1]`, and the "score model not configured" error. All with an injected fake evaluator, so no Azure dependency is needed.
- **G3 Spark adapter** (`spark.py`): row decoding and its error branches without a JVM. The `transform` path stays in `tests/test_spark.py`, which runs only where Java is installed.
- **G4 Cosmos storage** (`storage/cosmos.py`): the uncovered paths through the fake client that `tests/test_storage_cosmos.py` already uses.

### 4.3 No production change by default
The expected diff is tests, fixtures, component skills and log entries. A defect found while characterizing is recorded and healed under `heal-contract-failure`, in its own commit.

### 4.4 Component skills
Each group adds or extends a component skill that names its files, its contracts and its load-bearing constraints. Eight original files today are named by no skill.

### 4.5 What this decision does not do
- It does not set a coverage threshold. A numeric target would be invented; see the open question.
- It does not cover the 21 `scorers/` files, `cli.py`, or the remaining original files above 60%. They get their own decision once this set is done.
- It does not rewrite or deprecate any original module.

### 4.6 Test data
*Real:* the governance store (`AGENT_LEARNING_LOCAL_STORE_DIR`, the socialengage store) holds 60 recorded sets of the three metric results (180 results: 153 `completed`, 27 `skipped`) from real governance runs, written by the local evaluators (`local:intent`, `local:adherence`, `local:completion`, `local:episode-outcome`). They show the real `MetricResult` shape, including the `skipped` status, so G2 fixtures are small committed subsets of them. *Gaps, stated:* (1) that store sits outside this repository, so a CI checkout cannot read it; any record a contract uses is copied under `tests/fixtures/` (LL-037, LL-040). (2) The records come from the local evaluators in `metrics/local.py`, not from the Azure-backed wrappers in `metrics/task_completion.py`, `task_adherence.py` and `intent_resolution.py` that G2 characterizes, so those wrappers still run against an injected fake evaluator. (3) The normalized scores take only 0.5 and 1.0 (the 0.5 intent scores come from an unfitted classifier, `fitted: false`); no 0.0 outcome has been recorded. (4) The store holds no routing history, so `classifiers/router.py` fixtures are invented, small, and named as invented in each test. (5) `spark.py` and `storage/cosmos.py` have no recorded Spark or Cosmos run, so their fixtures are invented.

## 5. Alternatives Considered
- **Rely on Microsoft's tests alone.** Cheapest, and the original behavior is already mostly executed. It leaves no governed contract, no skill, and no way to tell a behavior change from a regression at the story level.
- **Raise coverage with unlabelled tests.** Moves the number without recording intent. A test with no Story or ADR header fails the contract discipline the rest of the repository follows.
- **Rewrite the weak modules under new ADRs.** Treats the original code as defective without evidence. It also changes behavior that adopters, including Microsoft's Scout integration, rely on.
- **Cover everything in one pass.** 54 files at once cannot be reviewed or healed in the loop's one-story-at-a-time shape.

## 6. Consequences
- Eight original files gain contracts that name a Story and this ADR, and the component skills gain entries for them.
- Behavior is pinned as observed. If upstream later changes one of these files, a contract fails and the change is a decision, not a surprise.
- A pinned bug stays pinned until it is healed on purpose. The finding is recorded so it is not mistaken for intended behavior.
- The work is catch-up. It is dated 2026-11-04, and nothing in it is backdated to the original code's authoring.
- Coverage numbers will rise, but they are reported as an observation and not used to declare the work done.

## 7. Architectural Invariants
1. **Characterize, do not redesign.** Contracts pin current behavior. Production code is untouched unless a finding is healed.
2. **One test per acceptance criterion**, with the Story and ADR named in its header.
3. **Findings are recorded, not absorbed.** A docstring-versus-behavior gap goes to a register and `heal-contract-failure`.
4. **No Azure or network dependency** in these contracts. Evaluators are injected fakes.
5. **JVM-only tests stay separate.** A contract that needs Java lives in `tests/test_spark.py`, and the log states when it was not run.
6. **Prospective approval only.** The documents for this work are approved at the time they are given, not backdated.

## 8. References
- `docs/project-docs/Pillar-Code-Map.md` (Draft) and `docs/project-docs/Project-Pillars.md`
- Pillar: Frozen-model, in-process learning
- ADR-002 (storage backend strategy), ADR-034 (tooling decommission), ADR-036 (methodology catalog and review triage)
- `.claude/skills/implement-story`, `.claude/skills/heal-contract-failure`
- `src/agent_learning/classifiers/`, `src/agent_learning/metrics/`, `src/agent_learning/spark.py`, `src/agent_learning/storage/cosmos.py`

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-11-04 | Proposed | Draft for catch-up governed contracts on the original SDK code. Not accepted. |
| 2026-11-04 | Test data corrected | §4.6 first said no recorded metric history exists. The governance store holds 180 real metric results (60 sets); §4.6 now states what they are and what they do not cover. Found when Menno asked whether the store holds sufficient evidence. |
| 2026-11-09 | Renumbered from ADR-039 to ADR-040 | The number 039 was also used by "Shadow-Gate Learning and the Review-Finding Corpus" (ADR-039, PR #165). The maintainer decided on 2026-11-09 that the shadow-gate ADR keeps 039 and this ADR becomes 040. The approval evidence recorded on 2026-11-04 (approve-adr episode `69365299`, and the files now named `adr-040-*` under `docs/policy-shapes/`) was written under the earlier number and is kept unchanged. This ADR is still Proposed in this file. |
| 2026-11-10 | Accepted | The maintainer confirmed the 2026-11-04 `approve-adr` outcome (episode `69365299`) after reviewing the score on 2026-11-10; the Status line, which still read Proposed, now records it. The open questions below stay open. |

## Open questions

- **Should a numeric coverage floor apply to these files?** This ADR sets none. Any figure would be a proposed threshold for Menno to confirm, not a measured one.
- **Which group goes first?** Proposed order G1, G2, G3, G4, because G1 and G2 need no external service. Menno decides.
- **Does `cli.py` get a governed contract now?** It is 88% covered with the fork's tests but has no Story or ADR behind it. Left for a later decision.
