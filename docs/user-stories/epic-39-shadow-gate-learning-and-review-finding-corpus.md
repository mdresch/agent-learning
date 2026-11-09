# Epic 39: Shadow-Gate Learning and the Review-Finding Corpus

**Source ADR:** [ADR-039](../adr/ADR-039-shadow-gate-learning-and-review-finding-corpus.md) — Accepted (2026-11-09, Menno); Episode `6b98f377-9ab1-4290-91a1-0832546037ea`  
**Source BRD/FDD:** [BRD-039](../project-docs/Business-Requirements/BRD-039-shadow-gate-learning-and-review-finding-corpus.md) / [FDD-039](../project-docs/Functional-Design/FDD-039-shadow-gate-learning-and-review-finding-corpus.md)  
**Status:** Approved (2026-11-09, Menno) — derived from Accepted ADR-039, BRD-039 and FDD-039 (Approved 2026-11-09); adjudicated via `approve-user-stories` (robust utility 0.665, episode `434556ab-df4e-4625-9667-d11b976b286f`). Menno confirmed FDD-039 D1 to D6 on 2026-11-09.

Six stories. Each rule sits in one story (LL-012). All new code is in `src/agent_learning_ext/` (BRU-039-15; LL-050). Contract tests: `tests/test_shadow.py` (39.1, 39.2), `tests/test_review_corpus.py` (39.3, 39.4, 39.5), `tests/test_shadow_cli.py` (the command criteria in 39.2, 39.3, 39.4), `tests/test_shadow_rituals.py` (39.6). BRU-039-12 (training stays gated) has no story of its own: no story here trains a policy, and the gates of ADR-003 and ADR-005 are unchanged. Adapters for #2 REINFORCE and #9 Thompson are a later story (FDD-039 §3.6).

Fixture for 39.2 ("the standard tier"): tier `standard` (floor 20), margin 0.05, `z` 1.96, `action_ids` `["a", "b"]`. Fixture for 39.3 to 39.5 ("the log"): a text block of triage lines in the ADR-036 shape, quoted in each criterion.

---

## Story 39.1 — The Shadow Record

**Status:** Ready — FDD-039 approved 2026-11-09  
**As** a maintainer, **I want** one validated, write-once shadow record on an episode, **so that** a learner's verdict is kept in a form that cannot be rewritten after the human decides.

### Acceptance Criteria

- **$AC_0$ (Four Keys):** `build_shadow("thompson/9", 3, "approve_adr", {"approve_adr": 0.7, "reject_adr": 0.3})` returns exactly the keys `shadow_learner`, `shadow_policy_version`, `shadow_action`, `shadow_probs`, with those values.
- **$AC_1$ (No Probabilities):** `build_shadow("ucb/10", "v2", "reject_adr")` returns `shadow_probs` `None` and the other three keys.
- **$AC_2$ (Bad Values Raise):** each of these raises `ValueError` and returns nothing: a learner name `"Thompson"` or `"thompson"` (no `/number`); an empty action; a probability `1.2`, `-0.1`, `nan` or `inf`; probabilities summing to `0.9`; probabilities that do not contain the action; an empty policy version.
- **$AC_3$ (Attach):** `attach_shadow({}, shadow)` leaves the four keys in the dict and returns `None`. Existing keys such as `task_completed` stay.
- **$AC_4$ (Write Once):** a second `attach_shadow` on the same dict raises `ValueError` and the dict equals what it was before the second call.
- **$AC_5$ (Human First Is Refused):** `attach_shadow` on a dict that already has `decision_disposition`, `correct_action_id` or `feedback_status` raises `ValueError` and leaves the dict unchanged.
- **$AC_6$ (Untouched Keys):** `shadow_low_action` and `shadow_entropy_bits` in the dict are not read, written or removed.
- **$AC_7$ (Pure):** `shadow.py` imports nothing from `agent_learning.storage` and nothing from `numpy`, and does not edit any Microsoft module.

---

## Story 39.2 — The Agreement Report

**Status:** Ready — FDD-039 approved 2026-11-09  
**As** a maintainer, **I want** an agreement report judged against the base rate, **so that** a learner that always predicts the majority action is never reported as tracking the human.

### Acceptance Criteria

- **$AC_0$ (Tracks):** on the standard tier, 10 human `a`, 10 human `b`, and shadow agreeing on 18 of 20: `n` 20, `k` 18, `base_rate` 0.5, `threshold` 0.55, `wilson_lower` 0.698962 within 1e-6, `status` `tracks`.
- **$AC_1$ (Does Not Track):** 14 human `a`, 6 human `b`, agreeing on 18 of 20: `base_rate` 0.7, `threshold` 0.75, `wilson_lower` 0.698962 within 1e-6, `status` `does_not_track`.
- **$AC_2$ (One Class):** 20 human `a`, shadow `a` on all 20: `base_rate` 1.0, `threshold` 1.05, `status` `not_testable`.
- **$AC_3$ (Too Few):** 19 qualifying episodes give `status` `insufficient` whatever `k` is. The floor is read from `AutonomyConfig.for_tier(tier).min_outcomes`, so tier `low` with 3 episodes is not `insufficient`.
- **$AC_4$ (Confusion):** human `[a, a, b]`, shadow `[a, b, b]`, tier `low`: `confusion` `{"a": {"a": 1, "b": 1}, "b": {"b": 1}}`, modal action `a`, `base_rate` 0.666667 within 1e-6, and for `b` precision 0.5 and recall 1.0.
- **$AC_5$ (Empty Denominator):** a non-modal action the learner never predicted has precision `None`; one that never occurred in the human actions has recall `None`.
- **$AC_6$ (Qualifying And Skipped):** an episode without `shadow_learner` or `shadow_action`, or whose human action is not in `action_ids`, is counted in `skipped` and not scored. The human action is `correct_action_id` when present, else `action_id`.
- **$AC_7$ (Per Learner And Tie-Break):** two learners in one call give two report entries. A tie for the modal action goes to the action that comes first in `action_ids`.
- **$AC_8$ (Tier Check):** a tier outside `low`, `standard`, `high`, `critical` raises `ValueError`.
- **$AC_9$ (Command):** `agent-learn-ext shadow-report --agent-id A --task-id T --tier standard` prints the report as JSON, writes nothing (the store's file count is the same before and after), and exits 0 with an empty `learners` list when no episode has a shadow record.

---

## Story 39.3 — The Corpus, Its Hold-Outs and Its Health

**Status:** Ready — FDD-039 approved 2026-11-09  
**As** a maintainer, **I want** the logged review findings parsed, the unreadable ones held out, and a health report computed by tooling, **so that** no learner is scored on a corpus I have not been shown to be fit.

### Acceptance Criteria

Fixture "the log": `Q-1-1 | logic error | verified: yes | decision: accepted | r | fix: aaa1111`, `Q-1-2 | test gap | verified: no | decision: accepted | r | fix: none`, `Q-2-1 | style | verified: no | decision: declined | r | fix: none`, `Q-2-2 | logic error | verified: yes | decision: declined | r | fix: none`, `Q-2-3 | crash risk | verified: unknown | decision: deferred | r | fix: none`, `Q-3-1 | logic error | verified: yes | decision: bogus | r | fix: none`, each wrapped in backticks.

- **$AC_0$ (Build And Order):** the five valid lines become rows in the order `Q-1-1, Q-1-2, Q-2-1, Q-2-2, Q-2-3`; the `bogus` line is in `unparsed` with its parser error. A line repeated in the input appears once.
- **$AC_1$ (Contradiction):** `Q-1-2` (`verified: no`, `accepted`) has `held_out` `contradictory` and `label` `None`. `Q-2-2` (`verified: yes`, `declined`) is not held out and has `label` `declined`.
- **$AC_2$ (Unknown):** `Q-2-3` has `held_out` `unknown_verified` and `label` `None`.
- **$AC_3$ (Health Counts):** `total` 6, `parsed` 5, `unparsed` 1, `contradictory` 1, `unknown` 1, `held_out` 3, `held_out_share` 0.5, `passes` `False`.
- **$AC_4$ (Threshold Pass):** a log of 40 `accepted` rows (one of them contradictory) and 20 `declined` rows (`held_out_share` 1/60, about 0.017) has `usable_by_action` `{"accepted": 39, "declined": 20}`, `trainable_actions` `["accepted", "declined"]` and `passes` `True`.
- **$AC_5$ (Contrast Needed):** a log of 60 `accepted` rows and nothing else has `passes` `False`, because only one action has 20 usable rows.
- **$AC_6$ (Improvements View):** with `known_modules` `["routing.py"]`, an `accepted` row whose reason says "routing.py divides by n" appears under `routing.py` with its finding id, claim type and fix commit; a `declined` row naming `routing.py` does not.
- **$AC_7$ (Command):** `agent-learn-ext review-corpus-report --paths <file>` prints the health report, the held-out rows and the unparsed lines, writes nothing, and exits 0 when a file has no triage lines (all counts 0, `passes` `False`).
- **$AC_8$ (Pure):** `review_corpus.py` imports nothing from `agent_learning.storage` and nothing from `numpy`.

---

## Story 39.4 — Registering the Corpus

**Status:** Ready — FDD-039 approved 2026-11-09  
**As** the maintainer, **I want** each usable finding registered once as a reconstructed episode, **so that** the corpus is in the store without anyone re-typing it or guessing a field.

### Acceptance Criteria

- **$AC_0$ (Episode Shape):** the episode for `Q-1-1` of Story 39.3's log has `agent_id` `agent-learning-governance`, `task_id` `triage-review-finding`, `action_id` `accept_and_amend`, and `metadata` containing the `to_episode_metadata` fields plus `reconstructed` `True`, `review_date` `"unknown"` and `fix_commit` `"aaa1111"`.
- **$AC_1$ (Actions):** `declined` maps to `decline_with_reason` and `deferred` to `defer_to_human`. A held-out row produces no episode.
- **$AC_2$ (Unknown Fix):** a row whose fix reads `none` has `fix_commit` `"unknown"`.
- **$AC_3$ (Stable Id):** the id is the same on two builds of the same finding and different for two findings.
- **$AC_4$ (Dry Run):** without `--write` the command prints how many episodes it would add and the store's file count is the same before and after.
- **$AC_5$ (Refusals):** `--write` exits 2 and writes nothing when the health report fails, when `triage-review-finding` has no policy in the store, or when `--store-confirmed` is absent.
- **$AC_6$ (Idempotent):** two runs of `--write` on a healthy corpus add the episodes once; the second run adds 0 files and says so.
- **$AC_7$ (Store Report):** the command prints the resolved store path and the file count before and after (LL-040).

---

## Story 39.5 — Time-Ordered Evaluation and the Baselines

**Status:** Ready — FDD-039 approved 2026-11-09  
**As** a maintainer, **I want** the corpus evaluated only on what came before each finding, **so that** a retrospective score cannot be inflated by training and scoring on the same record.

### Acceptance Criteria

- **$AC_0$ (Order):** rows with ids `Q-2-1`, `Q-1-2`, `Q-1-10`, `Q-1-1` are evaluated in the order `Q-1-1, Q-1-2, Q-1-10, Q-2-1` (the ordinal compares as a number).
- **$AC_1$ (Only The Past):** with a recording predictor, the prediction for the row at position `i` is made after `fit` was called with exactly rows `0..i-1`, and never with row `i` or a later row. The first row is not scored.
- **$AC_2$ (Modal Predictor):** on labels `[accepted, accepted, declined, accepted]`, `ModalPredictor` predicts `accepted` for rows 1, 2 and 3, and `k` is 2 of 3.
- **$AC_3$ (Claim-Type Predictor):** on rows `(logic, accepted), (style, declined), (style, ?)`, `ClaimTypePredictor` predicts `declined` for the third; with no earlier row of that claim type it falls back to the modal label.
- **$AC_4$ (Held-Out Rows):** held-out rows are neither fitted on nor scored.
- **$AC_5$ (Label):** the result carries `retrospective` `True`, and its report is computed at the `standard` tier by Story 39.2's report.
- **$AC_6$ (Not Shadow Evidence):** the result never carries a `shadow_learner` key and is not written to the store.

---

## Story 39.6 — The Rituals

**Status:** Ready — FDD-039 approved 2026-11-09  
**As** a maintainer, **I want** Step 8 and the gate review text to say "record the shadow verdict first", **so that** the habit exists before any learner is configured.

### Acceptance Criteria

- **$AC_0$ (Step 8):** `.claude/skills/implement-story/SKILL.md` Step 8 states that, when a shadow learner is configured, its verdict for each finding is recorded with `attach_shadow` before the triage `decision` is written.
- **$AC_1$ (Gate Reviews):** `.claude/skills/governance/SKILL.md` states that a gate review records the shadow verdict before the human decision, and that agents recommend and never approve.
- **$AC_2$ (Reports):** the same skill states that Stage 18 and the recap session report the §2.2 fields from `shadow-report`, with a `retrospective` result reported apart.
- **$AC_3$ (One Rule Each):** the new sentences cite ADR-039 and BRU-039-14 and add no second copy of the agreement rule (it lives in FDD-039 §3.2).
- **$AC_4$ (Guard):** `tests/test_shadow_rituals.py` fails if any of the three statements is removed, and `tests/test_governance_baseline.py` still passes.
- **$AC_5$ (No Propagation):** `sidpa-template` is not edited; the Tier 3 proposal is listed as a proposal in the log entry for a human to approve.
