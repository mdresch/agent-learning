# FDD-039: Shadow-Gate Learning and the Review-Finding Corpus

**Source ADR:** [ADR-039](../../adr/ADR-039-shadow-gate-learning-and-review-finding-corpus.md) — Accepted (2026-11-09, Menno); Episode `6b98f377-9ab1-4290-91a1-0832546037ea`  
**Source BRD:** [BRD-039](../Business-Requirements/BRD-039-shadow-gate-learning-and-review-finding-corpus.md)  
**Status:** Approved (2026-11-09, Menno) — derived from Accepted ADR-039 and BRD-039 (Approved 2026-11-09); adjudicated via `approve-fdd` (robust utility 0.684, episode `51350399-4baa-4d0d-b88f-3bb518e183f6`). Menno confirmed D1 to D6 on 2026-11-09, each as the proposal in §4 (see §7).

---

## 1. Architecture and Component Placement

1. **New module** `src/agent_learning_ext/shadow.py`. Pure functions on plain data: build and attach the shadow record, and compute the agreement report. It uses the standard library, `agent_learning_ext.autonomy.wilson_lower_bound` and `agent_learning_ext.config.AutonomyConfig`. It imports nothing from `agent_learning.storage` and nothing from `numpy`.
2. **New module** `src/agent_learning_ext/review_corpus.py`. Pure functions on text and plain data: build the corpus, hold out rows, report health, build the improvements view, produce episode dictionaries, and run the time-ordered evaluation. It imports `find_triage_lines`, `parse_triage_line`, `to_episode_metadata` and `TriageRecord` from `agent_learning.review_triage` (our own module, read only) and `agent_learning_ext.shadow`.
3. **CLI.** Three commands in `src/agent_learning_ext/cli.py`, reached through `agent-learn-ext`: `shadow-report` and `review-corpus-report` (read only), and `review-corpus-register` (writes only with `--write`). `agent-learn` is not touched.
4. **Why `agent_learning_ext`.** The fork rule (BRU-039-15). LL-050 recorded that Epic 22's documents named `src/agent_learning/weight_compiler.py` while the module belonged in `agent_learning_ext`. This FDD names the package once, here.
5. **No new record type, no `Episode` field, no store change.** Everything is `Episode.metadata` and generated output.
6. **Rituals.** `.claude/skills/implement-story/SKILL.md` Step 8 and the gate review text in `.claude/skills/governance/SKILL.md` gain one rule each (Story 39.7). They are text; no code runs them.

---

## 2. Data Contract

### 2.1 Shadow record (four keys in `Episode.metadata`)

| Key | Type | Rule |
|---|---|---|
| `shadow_learner` | str | `<name>/<methodology number>`, for example `thompson/9`; must match `^[a-z0-9][a-z0-9-]*/[0-9]+$` |
| `shadow_policy_version` | int or str | the policy version that produced the verdict; non-empty |
| `shadow_action` | str | a non-empty action id |
| `shadow_probs` | dict[str, float] or None | action id to probability; every value finite in [0, 1]; the sum is within 1e-6 of 1; contains `shadow_action`; None when the learner has no probabilities |

`shadow_low_action` and `shadow_entropy_bits` (ADR-021) are separate keys and are untouched.

### 2.2 Agreement report (per shadow learner)

`{"learner", "n", "k", "agreement", "modal_action", "base_rate", "wilson_lower", "floor", "margin", "threshold", "status", "confusion", "per_action"}`. `status` is one of `insufficient`, `not_testable`, `tracks`, `does_not_track`. `confusion` maps human action to a map of shadow action to count. `per_action` maps each non-modal action to `{"precision", "recall"}`, each a float or None when its denominator is 0.

### 2.3 Corpus row and health report

A row holds the parsed `TriageRecord`, its `label` (`accepted`, `declined`, `deferred` or None), and a `held_out` reason (`contradictory`, `unknown_decision`, `unknown_verified` or None). Parser-rejected lines are kept as `{"line", "error"}` in `unparsed`. The health report is `{"total", "parsed", "unparsed", "contradictory", "unknown", "held_out", "held_out_share", "usable_by_action", "trainable_actions", "thresholds", "passes"}`.

### 2.4 Registered finding episode

One `Episode` per parsed finding: `agent_id` `agent-learning-governance`, `task_id` `triage-review-finding`, `id` a `uuid5` of the finding id under a fixed namespace (so a rerun produces the same id), `action_id` from the logged decision (`accepted` to `accept_and_amend`, `declined` to `decline_with_reason`, `deferred` to `defer_to_human`; `unknown` or held-out rows are not registered), `metadata` = `to_episode_metadata(record)` plus `{"reconstructed": true, "review_date": "unknown", "fix_commit": <fix or "unknown">, "corpus_held_out": null}`.

---

## 3. Behavior

### 3.1 `build_shadow` and `attach_shadow`

`build_shadow(learner, policy_version, action, probs=None)` validates §2.1 and returns the four-key dict; a bad value raises `ValueError`. `attach_shadow(metadata, shadow)` raises `ValueError` and changes nothing when (a) any of the four keys is already in `metadata`, or (b) `metadata` already holds a human verdict key: `decision_disposition`, `correct_action_id` or `feedback_status`. Otherwise it adds the four keys. It returns None.

### 3.2 `agreement_report`

`agreement_report(episodes, action_ids, tier, margin=0.05, z=1.96)` takes episodes as mappings or objects with `metadata` and `action_id`. An episode qualifies for a learner when `metadata["shadow_learner"]` and `metadata["shadow_action"]` are strings and its human action (`metadata["correct_action_id"]` when present, else `action_id`) is in `action_ids`. Episodes that do not qualify are counted in `skipped`, never scored. Per learner: `n` is the qualifying count, `k` the count where shadow equals human, the modal action is the most frequent human action (ties broken by the order of `action_ids`), `base_rate` its share of `n`, `floor = AutonomyConfig.for_tier(tier).min_outcomes`, `threshold = base_rate + margin`, and `wilson_lower = wilson_lower_bound(k, n, z)`.

Status, tested in this order: `n < floor` gives `insufficient`; else `threshold > 1` gives `not_testable` (one class, or nearly one); else `wilson_lower > threshold` gives `tracks`; otherwise `does_not_track`. Precision for a non-modal action is true positives over shadow predictions of it; recall is true positives over human occurrences of it.

### 3.3 Worked checks (tier `standard`, floor 20, margin 0.05; to be re-run when built)

| Case | Human actions | n, k | base_rate | threshold | wilson_lower | status |
|---|---|---|---|---|---|---|
| C1 | 10 `a`, 10 `b` | 20, 18 | 0.5 | 0.55 | 0.698962 | `tracks` |
| C2 | 14 `a`, 6 `b` | 20, 18 | 0.7 | 0.75 | 0.698962 | `does_not_track` |
| C3 | 20 `a` | 20, 20 | 1.0 | 1.05 | 0.838870 | `not_testable` |
| C4 | 19 episodes | 19, any | — | — | — | `insufficient` |

Confusion check: human `[a, a, b]`, shadow `[a, b, b]`, tier `low`, floor 3, gives `confusion {"a": {"a": 1, "b": 1}, "b": {"b": 1}}`, modal action `a`, base_rate 0.666667, and for `b` precision 0.5 and recall 1.0.

### 3.4 Corpus health thresholds (decision D2)

`passes` is true only when `held_out_share <= 0.05` **and** at least two actions have at least 20 usable rows. `held_out_share = (contradictory + unknown + unparsed) / total`. The reason for 0.05: it equals the agreement margin, so holding out those rows cannot move any class share by more than the margin the agreement rule already tolerates. The reason for 20: the `standard` tier floor, the lowest floor that rests on a confidence bound. An action with fewer than 20 usable rows is left out of `trainable_actions` and is not scored. A contradiction is `verified == "no"` with `decision == "accepted"` (ADR-039 §4.4 item 2). A `verified: yes` row that was declined is not a contradiction; it is the "true but not worth the change" class and is kept.

On the 2026-11-09 run this reads 223 total, 221 parsed, 2 unparsed, 2 contradictory, 0 unknown, so a held-out share of 4/223 = 0.018. The report recomputes it; the figure here is not the contract.

### 3.5 Registration (`review-corpus-register`)

Default is a dry run that prints how many episodes it would add. `--write` calls the same registration path as `task-episode-register` for each episode in §2.4 whose id is not already in the store. It prints the store path and the file count before and after (LL-040). It refuses with exit 2 when the health report fails, when `triage-review-finding` has no policy in the store, or when `--write` is given without `--store-confirmed`. An agent never passes `--write` on its own.

### 3.6 Time-ordered evaluation

`evaluate_retrospective(rows, predictor)` orders usable rows by `(pr, ordinal)`, where the ordinal is the third part of the finding id. For each row at position `i >= 1` it calls `predictor.predict(row)` having called `predictor.fit` only on rows `0..i-1`, records the prediction, then moves on. The result is a list of `(finding_id, predicted, human)` plus the same agreement report as §3.2, with `status` computed at the `standard` tier, and the label `retrospective`. A predictor protocol has `fit(rows)` and `predict(row) -> dict[str, float]`. Two reference predictors ship: `ModalPredictor` (the most frequent label so far) and `ClaimTypePredictor` (the most frequent label so far for that claim type, falling back to the modal one). Adapters for #2 REINFORCE and #9 Thompson are not specified here. `ReinforceLearner` needs a sampled `action_logprob` and Thompson has its own policy, so reading those interfaces may change the design. They follow in a later story, after Story 39.5 has reported what the two baselines score, because a learner has to beat `ClaimTypePredictor` to be worth shadowing.

### 3.7 Improvements view

`improvements_view(rows, known_modules)` takes accepted rows whose `reason` or `fix` text names a module in `known_modules` (a file name such as `routing.py`, matched as a whole word, or a path under `src/agent_learning` or `src/agent_learning_ext`) and groups them by module: `{module: [{"finding_id", "claim_type", "fix_commit"}]}`, largest group first. It is printed by `review-corpus-report --improvements` and never saved.

### 3.8 Commands

- `agent-learn-ext shadow-report --agent-id A --task-id T --tier standard [--margin 0.05]` reads the task's episodes from the store and prints the §2.2 report per learner as JSON. It writes nothing. No episode with a shadow record exits 0 with an empty `learners` list.
- `agent-learn-ext review-corpus-report --paths <files...> [--improvements]` prints the §2.3 health report, the held-out rows and the unparsed lines. It writes nothing.
- `agent-learn-ext review-corpus-register` as in §3.5.

---

## 4. Points ADR-039 left open (confirmed by Menno, 2026-11-09)

- **D1 — Margin and rule.** Proposal: margin 0.05, the same constant as `DecisionFrame.minimum_margin`, and the rule in §3.2 with `z = 1.96`. Alternative: derive the margin per gate from its episode count. Reason for the proposal: one constant that already exists in the project, and the Wilson bound already penalises small samples.
- **D2 — Corpus-health thresholds.** Proposal: §3.4 (held-out share at most 0.05; two actions with at least 20 usable rows). Alternative: a stricter 0.02.
- **D3 — Ordering key.** Proposal: `(pr, ordinal)` as the ADR says. The log carries no review date, so date ordering is not available.
- **D4 — Reviewer and revision fields.** Proposal: the reviewer is `metadata["reviewer"]` (already in `to_episode_metadata`), the revision is `metadata["fix_commit"]`, and the review date is `unknown` for every reconstructed finding.
- **D5 — Registration identity.** Proposal: `uuid5` of the finding id, so registration is idempotent. Alternative: a random id plus a lookup by `finding_id`, which costs a store scan on every run.
- **D6 — Policy initialization.** ADR-036 and FDD-036 left `triage-review-finding` and `route-review-finding` uninitialized. Proposal: Menno runs `task-policy-init` for `triage-review-finding` (full authority, `requires_human_approval: true`) before the first `--write`; the command refuses otherwise. Initializing `route-review-finding` waits until a trained learner is considered.

---

## 5. Error Handling

- A bad shadow value, a repeated shadow key, or a shadow write after a human verdict key raises `ValueError`; `metadata` is unchanged.
- A tier that is not `low`, `standard`, `high` or `critical` raises `ValueError`.
- A command with a missing path exits 2 and writes nothing. A parse failure on one line goes to `unparsed`; it does not stop the run.
- `review-corpus-register --write` exits 2 on a failed health report, a missing policy, or a missing `--store-confirmed`, and writes nothing.

---

## 6. Out of Scope

Promotion of any learner; a gate's authority; shadow runs at the ADR, BRD and FDD gates (they hold only approvals; revisit when a rejection or revision episode exists); `trace_id`; off-policy evaluation; other reviewers; propagation to `sidpa-template`.

---

## 7. Confirmed bounds

Menno confirmed D1 to D6 on 2026-11-09, each as the proposal in §4: D1 margin 0.05 with the Wilson rule at `z = 1.96`; D2 held-out share at most 0.05 and at least two actions with 20 usable rows; D3 order by `(pr, ordinal)`; D4 `reviewer`, `fix_commit` and `review_date` `"unknown"`; D5 a `uuid5` of the finding id; D6 Menno runs `task-policy-init` for `triage-review-finding` before the first `--write`.
