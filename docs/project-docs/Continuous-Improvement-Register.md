# Continuous Improvement Register (Organizational Process Assets)

**Origin:** Instantiated from the `sidpa-template` Continuous Improvement Register (commit `6471422`).  
**Lifecycle Role:** Positive, generative counterpart to the [Lessons Learned Register](Lessons-Learned-Register.md). Held once per epic, after its last user story, as part of `implement-story` Step 9.  
**Maintenance Rule:** Append-only. A recap with nothing new is recorded as a short sign-off line in the Epic Recap Log.  
**Downstream Feed:** Stages 16/17 (in-flight fast-path change) and Stage 18 (`Intent Refinement`).

---

## 1. Purpose

The Lessons Learned Register takes a defensive posture: traps, defects and root causes. This register takes the positive one. It captures improvement ideas, architectural simplifications, developer-experience boosts and product opportunities while the knowledge from an epic is fresh.

### The mandatory per-epic cadence questions

At the epic's last story (Step 9), ask the code question first, then the improvement question.

**1. The code question** (answered in the epic's *Code & Methodology Recap*, section 3):

> *"What did this epic's code implement (which methodology, which modules and public names), what in the code is worth reusing, where is it weakest, where in this project could it be applied, and what would a demonstration show?"*

Answer it from the merged code and the review record, not from the plan: name files and public names, count review findings per module from the `Q-<PR>-<n>` lines with the project's parser, and say what is measured and what is only claimed. Procedural lessons (git, environment, review workflow) are not the subject of this question; they go to the Lessons Learned Register.

**2. The improvement question:**

> *"What improvement ideas, architectural simplifications, developer-experience boosts, or product opportunities emerged during this Epic that could add value to upcoming Epics or roll into the Intent Refinement Proposal for the next phase?"*

- **Ideas emerged:** record each as an `IMP-###` entry in section 2.
- **None emerged:** record `Epic [N] Recap: No new improvement ideas identified.` in section 3.

### Dispositions

1. **`In-Flight Candidate`:** can be introduced in the active phase without expanding baseline scope. Evaluated through the governance change pipeline (Stages 16 to 17).
2. **`Rolled into Phase Next Intent Refinement`:** valuable but beyond the current baseline. Harvested at Phase Close (Stage 18) into the next phase's Intent Refinement.

An entry records only what the epic's work actually surfaced. Do not seed this register with examples or speculative ideas.

---

## 2. Improvement Ideas

| ID | Originating Epic | Idea Title | Category | Description & Technical Value | Target Benefit / Outcome | Disposition |
|---|---|---|---|---|---|---|
| IMP-001 | Epic 15 | Provision a story worktree and log a no-finding review with one command each | Developer experience | `scripts/complete_story.py` gains `worktree <story>` (git worktree add, `uv sync --all-extras`, remove the real `azure-cosmos`; LL-033) and `triage --none` (the prose line of LL-034), and appends the `Co-Authored-By` trailer to its commits. All three were repeated by hand in each of the six stories. | Fewer false REDs and CI failures per story | In-Flight Candidate |
| IMP-002 | Epic 15 | Make the Thompson sampling record self-describing | Architectural simplification | Add the policy id (the snapshot id used as the HMAC key) to the FDD-015 §2.3 record, so `replay(record)` needs no second argument and a record stays replayable after a learner update gives the snapshot a new id (interpretations I2 and I5; FDD-015 §7 item 6). | An auditor can replay a draw from the record alone | In-Flight Candidate |
| IMP-003 | Epic 15 | Find the failure history that HYP-AL-002 needs | Product opportunity | Story 15.6 could only show consistency on an all-accepted history. A low-authority policy with at least 100 scored episodes including failures would let the Thompson-versus-REINFORCE question be answered with data (BRD-015 BRU-015-10). | Evidence for or against adopting Thompson sampling in a decision | Rolled into Phase Next Intent Refinement |
| IMP-004 | Epic 19 | Read a stored meta-prior back into a `MetaPrior` | Architectural simplification | `seed_values` takes a `MetaPrior`, but `task-policy-meta-compile` stores a `PolicySnapshot`. Epic 20's `task-policy-warm-start --meta-prior` (Story 20.5) has to rebuild the `MetaPrior` from the snapshot's metadata. One small, tested function that does it (and refuses a snapshot that is not a meta-prior) would be shared by that command and by any reader. | Story 20.5 does not re-derive the shape | In-Flight Candidate |
| IMP-005 | Epic 19 | Read a Thompson policy by the probability that each action is the best | Product opportunity | ADR-003 §4.6 gates a posterior policy on normalised payoff rates, a proxy that cannot be met when several actions have similar rates (FDD-019 §7 items 8 to 10). A seeded Monte Carlo draw from the posteriors, or the closed form for two actions, gives the probability of being best and can use thresholds calibrated for it. | A Thompson policy with several plausible actions can earn autonomy on evidence | Rolled into Phase Next Intent Refinement |
| IMP-006 | Epic 19 | Commit a small recorded-store fixture so real-data checks run in CI | Developer experience | `data/agent-learning/` is git-ignored, so Story 19.7 rebuilds a store from committed episodes, action files and decision results and checks the recorded store only where it exists (FDD-019 §7 item 11). A committed, minimal export of the governance store (policies and active pointers, not secrets) would let such checks read the real thing everywhere. | Real-data tests are identical on every machine | In-Flight Candidate |
| IMP-007 | Epic 19 | One command for an approval run: frame, decide, compare, register | Developer experience | Approving the ADR, the FDD and the stories took a frame builder, a decision, a comparison script, an adjudication and an episode builder each time, six hand-written scripts, and one run checked the wrong store (LL-040). A `scripts/approve.py` that takes scores, prints the resolved store path, runs the steps, shows the comparison and registers only on an explicit flag would remove that. | Fewer mistakes and a repeatable audit trail per approval | In-Flight Candidate |
| IMP-008 | Epic 19 | Move the posterior-gate story out of Epic 19 | Architectural simplification | Story 19.8 changes `autonomy.py`, outside the epic's scope; the `approve-user-stories` comparison classified the epic as a regression for that reason (scope correctly bounded -0.030) and Menno accepted it. Epic 3, the autonomy-gate epic, is its natural home. | Epic 19 keeps its scope; the gate change sits with the gate | Rolled into Phase Next Intent Refinement |
| IMP-009 | Epic 20 | Share the real-data test helpers | Developer experience | Stories 19.7 and 20.6 each carry their own copy of `_recorded_tasks`, `_build_store` and `_tree` (rebuild a temporary store from `docs/policy-shapes/`). Amazon Q flagged the same unguarded `policy_id` read in both (Q-98-1, Q-101-1), and Story 21.7 needs a third copy. One shared helper module (or fixture) fixes a defect once and makes the git-ignored-store rule (FDD-019 §7 item 11, FDD-020 §7 item 7) live in one place. | A review finding on real-data tests is fixed once, not per story; Story 21.7 starts from the helper | Rolled into Phase Next Intent Refinement |
| IMP-010 | Epic 20 | Report which stored policies could donate | Product opportunity | Story 20.6 showed that no usable warm-start donor exists, but only as a test result. A read-only command (for example `task-policy-donor-candidates`) would list each stored policy with its authority, episodes seen, updates applied, whether its logits are non-zero and whether `assess_autonomy` is met, and the reason each cannot donate. HYP-AL-008 needs one converged low-authority donor and a cold same-family target; this shows when they exist. | The missing real donor is detected from the store, not rediscovered by hand; input to the HYP-AL-008 test plan | Rolled into Phase Next Intent Refinement |
| IMP-011 | Epic 20 | Flag stories whose status disagrees with the log | Developer experience | Stories 20.1 to 20.3 stayed `Ready` after they were built and logged; found only when Story 20.6 was opened. A small check (script or test) that fails when an `implementation-log.md` entry exists for a story whose status is not `Completed`, or the reverse, would catch status drift at review time. | Epic status lines can be trusted when planning the next phase | Rolled into Phase Next Intent Refinement |
| IMP-012 | Epic 20 | Detect an existing story branch or worktree before Step 0 | Developer experience | Extends IMP-001's `worktree <story>` command: if `feat/story-<X.Y>` or its worktree already exists, print the branch, `git status --short`, the commits ahead of `main` and the story's log entry, and point to `heal-contract-failure` (the rule added to `implement-story` Step 0 in PR #105). In Story 20.6 a started run was adopted because nothing stopped it. | A started run is healed from Intent, never adopted or implemented twice; the rule is enforced by the tool, not only by the skill text | Rolled into Phase Next Intent Refinement |
| IMP-013 | Epic 20 | Build the Cosmos test fakes' exceptions in one place | Developer experience | `tests/test_storage_cosmos.py` constructed `azure-cosmos` exceptions with the message as the first positional argument; the SDK now formats that argument as a status code, so four Story 2.1 contract tests failed on `main` until PR #102. A single helper that builds the fake exceptions with `status_code` and `message` (or a CI run against the latest SDK) shows this kind of SDK drift where it starts. | SDK changes break one helper, visibly, not four contract tests in an unrelated story | Rolled into Phase Next Intent Refinement |
| IMP-014 | Phase 1 close | Move the Stage 18 tooling onto the path ADR-034 keeps | Architectural simplification | `evaluate_phase_close_readiness`, hypothesis adjudication and `seed-next` exist only in the legacy `pmbok/` tree that ADR-034 plans to delete, and their tests are excluded from CI (INSIGHT-003, LL-043, AUDIT-004). Port them to `src/agent_learning/pmbok/` as pure functions with tests CI runs, or amend ADR-034 to keep them, before Stories 34.4 and 34.5 delete the tree. | Phase close tooling that CI protects and that survives the decommissioning | Rolled into Phase Next Intent Refinement |
| IMP-015 | Epic 14 | Export PR review comments into committed fixtures for offline replay | Developer experience / Test data | Automate export of Amazon Q review comment threads into committed offline fixtures (`tests/fixtures/critique/`) so Story 14.5 can run deterministically without network calls or manual scraping. | Unblocks Story 14.5 real triage replay and enables automated validation of HYP-AL-005 | In-Flight Candidate |
| IMP-016 | Epic 14 | Multi-Reviewer and Bugbot Ingestion in PR Gatekeeper | Developer experience / Governance | Extend `convert_unstructured_review_to_tags` in `scripts/pr_gate.py` to parse Cursor Bugbot, Claude, and human markdown review summaries into Epic 14 rubric deltas. | Eliminates manual tag authoring for non-Amazon-Q reviewers; ensures all reviewer critiques shift Bayesian support consistently. | In-Flight Candidate |
| IMP-017 | Epic 14 | PR Review-Triage Table Auto-Ingestion | Architectural simplification | Wire `agent-training-ext/triage_replay.py` into `pr_gate.py` to automatically detect and extract human triage table rows (`Q-<PR>-<n>`), replaying them so accepted defects penalize support and declined false alarms do not. | Human maintainer triage decisions are directly and automatically respected by the gatekeeper without manual formula overrides. | In-Flight Candidate |
| IMP-018 | Epic 14 | Empirical Reviewer Reliability Weighting | Product opportunity | Use the 139 real triage records from `tests/fixtures/critique_evidence/triage_replay_dataset.json` to compute reviewer trust/precision per claim type, applying calibrated doubt shifts ($\Delta d$) rather than raw support shifts alone. | Prevents uncalibrated bot reviewers with high false-alarm rates from halting valid PRs while preserving safety on crash risks. | Rolled into Phase Next Intent Refinement |
| IMP-019 | Epic 14 | Passive Governance Learning Harvester | Developer experience / ML Pipeline | Automate harvesting historical triage lines (`Q-<PR>-<n>`) and gate decisions from `implementation-log.md` into auditable `Episode` records and preference pairs in `data/agent-learning/store/`. | Seeds the LearningStore with real human governance choices, giving passive learners (such as PairwiseLearner) empirical training data. | In-Flight Candidate |
| IMP-020 | Epic 14 | Pre-Flight Spec Gate Rubric Standardization | Architectural simplification | Unify adversarial spec findings in `scripts/spec_gate.py` directly with the Epic 14 rubric (`specification_completeness`, `testability`, `upstream_fork_purity`, `architectural_boundaries`). | Guarantees mathematical and conceptual symmetry between pre-flight spec readiness and PR gatekeeper evaluations. | In-Flight Candidate |
| IMP-021 | Epic 16 | Continuous-Domain Parameter Widening Guard in Spec Auditor | Architectural simplification / Governance | Teach `spec_gate.py` to explicitly detect and flag when classical discrete primitives (e.g. Wilson score interval) are widened to continuous domains ($[0, \text{total}]$ with float successes), generating rationale tags for PR reviewers. | Eliminates repetitive review debate cycles across future bandit and exploration policies (e.g., Epic 17 Epsilon-Greedy). | In-Flight Candidate |
| IMP-022 | Epic 16 | Public Ingestion Guard Ordering Pattern (Deduplication First) | Architectural simplification / Reliability | Standardize batch-ingestion loops in policy statistics and storage writers (`add_rewards`, `store_episodes`) to place the duplicate-skip check (`if id in seen: continue`) ahead of value and schema validation. | Ensures idempotent replay of heterogeneous batches containing legacy/foreign records without spurious validation halts on already-consumed data. | In-Flight Candidate |
| IMP-023 | Epic 16 | Low-Authority Exploration Dataset Generation for HYP-AL-009 | Product opportunity | Build a synthetic low-authority benchmark simulator that generates mixed successes and failures (at least 100 scored episodes) to empirically benchmark UCB-1, Wilson-UCB, and Thompson sampling against REINFORCE on non-positive-only reward regimes (BRU-016-11). | Empirically resolves HYP-AL-009 with statistical significance rather than relying solely on positive-only consistency replays. | Rolled into Phase Next Intent Refinement |
| IMP-024 | Epic 18 | Strict Floating-Point Zero-Rel-Tol Auditor in Spec Gate | Developer experience / Testability | Enhance `scripts/spec_gate.py` to identify floating-point assertions that specify `abs_tol` without explicit `rel_tol=0.0` or direct absolute difference checks, warning when default `rel_tol=1e-9` could silently relax tight contracts ($10^{-12}$). | Guarantees test contracts enforce exact mathematical invariance without silent tolerance relaxation. | In-Flight Candidate |
| IMP-025 | Epic 18 | Automated Preference Pair Adapter from Curated Triage Dataset | ML Pipeline / Ingestion | Wire `tests/fixtures/critique_evidence/triage_replay_dataset.json` (139 human triage decisions) into a preference pair loader feeding `PairwiseLearner` directly via `TrainingRunner`. | Provides empirical human code review preferences to calibrate discrete governance decision policies offline. | In-Flight Candidate |
| IMP-026 | Epic 18 | Synthetic Red Team Pair Set for Discrete Policy Robustness | Product opportunity / Governance | Implement the unbuilt Red Team pair set (BRU-018-12) derived from the 3 adversarial and 6 diff governance fixtures to stress-test `PairwiseLearner` under adversarial preference overrides. | Empirically stress-tests policy divergence bounds under targeted adversarial perturbation. | Rolled into Phase Next Intent Refinement |
| IMP-027 | Epic 17 | Dual-Access Invocation Pattern (Callable Property Wrapper) for Extension Policies | Architectural simplification / Developer experience | Standardize `CallableSnapshot` and `CallableActionList` into a shared utility (`agent_learning_ext.policy.base_compat`) so that any custom policy implementing upstream `Policy` abstract methods can be seamlessly accessed as both methods (`policy.snapshot()`, `policy.actions()`) and attributes (`policy.snapshot.metadata`, `policy.actions`). | Eliminates calling convention mismatches between upstream runner harnesses and modern test assertions across all future extension policies. | In-Flight Candidate |
| IMP-028 | Epic 17 | Automated Action Space Reversibility Linter and Declarative Registry | Developer experience / Governance | Build an automated linter and CLI command (`task-policy-lint-reversibility`) that scans `docs/policy-shapes/*.actions.json`, validates strict boolean typing of `"parameters": {"reversible": bool}`, and flags unflagged action definitions where human maintenance could safely enable bounded exploratory probing. | Gives maintainers an explicit inventory of candidate reversible actions, allowing scheduled exploration to be deliberately unblocked without risking destructive actions. | In-Flight Candidate |
| IMP-029 | Epic 17 | Multi-Policy Offline Benchmarking Harness with Synthetic Failure Injection | Product opportunity / Research | Implement the out-of-scope benchmark comparing REINFORCE, UCB, Thompson sampling, and Scheduled Epsilon-Greedy on simulated task environments with known failure modes and controlled non-positive rewards, evaluating regret, convergence speed, and safety violation rates. | Empirically proves or disproves HYP-AL-009 on heterogeneous reward landscapes rather than purely positive-only history. | Rolled into Phase Next Intent Refinement |
| IMP-030 | Epic 22 | Check review-triage lines inside the PR gate | Developer experience / Governance | `scripts/pr_gate.py` runs `review_triage.parse_triage_line` over the triage lines added by the PR and halts on any claim type, verification or decision outside the vocabulary. | A line like `Q-145-2, auditability` (LL-049) is caught before merge instead of failing three foreign contracts on `main`. | In-Flight Candidate |
| IMP-031 | Epic 22 | Backfill Tier 2 targets for LL-045 to LL-048 and script the LL-041 check | Governance / Process | The Step 9 propagation check found no LL-045, LL-046, LL-047 or LL-048 id in any named Tier 2 target (`implement-story`, `pairwise-preference`, `ucb`, `critique-evidence` skills, `scripts/spec_gate.py`, `src/agent_learning_ext/policy/`). Add the rules to those targets and turn the grep into a small script that lists missing ids. | Lessons reach the files agents actually read, and the check stops depending on a person remembering it. | In-Flight Candidate |
| IMP-032 | Epic 22 | Generate the Project Status Register's repository facts from git | Developer experience | The register's last base commit, merged-PR state and next-story line were three facts stale one day after they were written. Derive them in `scripts/phase_rollup.py` (or a sibling) and leave only the narrative by hand. | Resuming after a session limit never starts from a wrong position. | Rolled into Phase Next Intent Refinement |
| IMP-033 | Epic 22 | Make the PR gate read the latest review per head commit and honour resolved findings | Developer experience / Governance | `scripts/pr_gate.py` takes, per bot author, the latest body containing words such as `review summary` or `blocking issues`. A `/q confirm` answer that lists every finding as resolved carries none of those words, so the gate kept scoring the round-1 review (five findings, margin -0.072) and halted a PR whose findings were all fixed and confirmed. Select reviews by `commit_id == headRefOid` and read a confirmation table's resolved rows. Its final status line also crashes on a cp1252 console (`UnicodeEncodeError`); print with a safe encoding. | The gate reflects the current head instead of a stale review, and no one is tempted to bypass it. | Implemented (PR #147) |
| IMP-035 | Epic 22 | Decouple Pareto Pruning from Feasible Margin Calculation in Scored Search | Algorithm / Compiler | In `weight_compiler.evaluate()`, compute robust margin across all constraint-feasible options (`assessment.feasible`), ensuring decisive victories register high confidence margins (+0.80) rather than zero (0.0). | Restores the multi-objective optimization gradient on audited real-world data and prevents Pareto dominance from zeroing out confidence margins. | Rolled into Phase Next Intent Refinement |
| IMP-036 | Epic 22 | Red Team Benchmark Dataset for Scored-Search Weight Compilation | ML Pipeline / Training | Ingest `tests/fixtures/red_team_adrs/` (ADR-900 to 910) to construct a balanced, multi-class governance dataset, allowing `policy-compile-weights` to learn weights that actively catch architectural anti-patterns. | Provides the required counterfactual and rejection labels to calibrate non-trivial criteria weights and prevent single-class simplex vertex collapse. | Rolled into Phase Next Intent Refinement |
| IMP-037 | Epic 38 | Let `train` call `ContextualReinforceLearner` | Product opportunity / Developer experience | Today `train` skips a contextual snapshot (BRU-038-11), so only API callers can train a contextual policy. Add a path in which `train` builds the learner for `policy_kind` `contextual_softmax` and reads `feature_vector` from the episodes. This changes the scope of BRD-038, so it needs an ADR and BRD amendment first. | Operators can train a contextual policy from the CLI, which closes the loop that Epic 38 opened for init and decide. | Rolled into Phase Next Intent Refinement |
| IMP-038 | Epic 38 | Helper that copies the decide payload's `feature_vector` onto the episode | Developer experience | `task-policy-decide` returns the vector it used and the caller must copy it onto the episode (FDD-038 D1). If the caller forgets, `ContextualReinforceLearner` skips every episode under `skipped_missing_vector`. Add a small capture helper, and consider warning when a contextual policy's episodes have no vector. | Removes the easiest way to train on nothing. | Rolled into Phase Next Intent Refinement |
| IMP-039 | Epic 38 | Close the two Epic 38 known gaps (Q-159-1 and the `autonomy` block) | Governance / Correctness | `task-policy` still prints an `autonomy` block computed from the unused logits for a contextual snapshot, and `task-policy-authority-set` from a hand-made full-authority contextual snapshot to `low` records a migration distribution from those logits. FDD-038 D4 specifies only the refusal to `full`. Decide the behaviour, amend FDD-038 through `scripts/stage16_amend.py`, then fix. | Removes the last outputs that read the unused scalar logits of a contextual policy. | In-Flight Candidate |
| IMP-040 | Epic 38 | Update demo 04 to use the packaged learner and move catalog row #4 | Documentation / Product opportunity | `examples/methodologies/04-contextual-bandit/` still writes the update by hand and the catalog keeps methodology #4 as `example_only`. Rewrite the demo on `task-policy-init --feature-dim`, `decide --features` and `ContextualReinforceLearner` with simulated rewards labelled synthetic (ADR-036 labeling contract). Move the catalog state only through the ADR-024 route once an adopter uses the learner. Extends IMP-023 and IMP-029, which already propose a synthetic benchmark. | Shows the packaged path end to end and removes a copy of the loop. | Rolled into Phase Next Intent Refinement |
| IMP-041 | Epic 38 | Trial a contextual policy on `escalate-diff-response` with the Stage 16 measurements as features | Product opportunity | The Stage 16 pipeline already measures numeric inputs for each amendment (change ratio, terms kept, downstream references, status line changed). They are natural features for a low-authority decision with three actions. Episode volume is very small today, so run it as a shadow comparison, never as authority. | Tests whether context improves the escalation choice on real governance data. | Rolled into Phase Next Intent Refinement |
| IMP-042 | Epic 38 | Compare a contextual learner with the claim-type baseline on `route-review-finding` | Product opportunity | Use the Epic 39 retrospective evaluator on the 221 parsed Q findings, with claim type, reviewer reliability and PR size as features. A contextual learner is worth shadowing only if it beats `ClaimTypePredictor`. Depends on Epic 39 being implemented. | Gives the first real test of whether a contextual learner adds anything on project data. | Rolled into Phase Next Intent Refinement |
| IMP-043 | Epic 38 | Union merge for the append-only `implementation-log.md` | Developer experience | Five merges in Epic 38 conflicted in `implementation-log.md` because every story appends at the same tail. Add a `.gitattributes` entry with the union merge driver for that file, or script the resolution, and keep the entries in merge order. Check that it does not hide a real edit conflict in an older entry. | Removes a conflict that recurs at every stacked or parallel story merge. | In-Flight Candidate |
| IMP-044 | Epic 38 | Align `implement-story` Step 0 and Step 6 with the whole-suite rule | Developer experience | Step 6 still lists `--ignore=tests/test_spark.py --ignore=tests/pmbok`. `tests/pmbok` collected fine once `uv sync --extra dev --extra examples` installed PyYAML (2498 passed, 3 skipped on the Story 38.6 tip), and the Spark tests skip without a JVM. Change the skill text to plain `uv run pytest` and add the sync command to Step 0. | Stops the skill and the agents it briefs from excluding tests that run. | In-Flight Candidate |

---

## 3. Epic Recap Log

One entry per epic recap, appended in the order held. Format:

```
### Epic <N>: <title>
- **Cadence Date:** <YYYY-MM-DD>
- **Code & Methodology Recap:**
  - **Methodology:** <name, catalog number, governing ADR, catalog state and hypothesis status (recorded, not changed by the recap)>
  - **Code delivered:** <modules, public names, CLI commands, contract test files>
  - **Design worth keeping:** <what the code does well, with the file and the rule>
  - **Review findings by module:** <counts per module and claim type from the Q-<PR>-<n> lines, with the accepted ones named>
  - **Known gaps in the code:** <what is not handled, with IMP ids>
  - **Where it could apply:** <policies or decisions in this project, and the data volume that limits them>
  - **Demonstration:** <what a runnable example should show, labelled synthetic where it is>
  - **Evidence status:** <what is verified by tests or measurement, and what is only claimed>
- **Defensive Review (LL-###):** <LL ids or no-new-lessons>
- **Positive Improvement Harvest:** <IMP ids, or "Epic <N> Recap: No new improvement ideas identified.">
```

An entry made before this format (Epics 14 to 22) has no code recap and is not rewritten; the register is append-only.

---

### Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling)
- **Cadence Date:** 2026-11-03
- **Defensive Review (LL-###):** LL-033, LL-034, LL-035
- **Positive Improvement Harvest:** IMP-001, IMP-002, IMP-003

---

### Epic 19: Hierarchical Meta-Prior Compilation Across Task Families
- **Cadence Date:** 2026-11-04
- **Defensive Review (LL-###):** LL-036, LL-037, LL-038, LL-039, LL-040
- **Positive Improvement Harvest:** IMP-004, IMP-005, IMP-006, IMP-007, IMP-008

---

### Epic 20: Explicit Policy Prior Warm-Starting
- **Cadence Date:** 2026-11-04
- **Defensive Review (LL-###):** LL-041, LL-042
- **Positive Improvement Harvest:** IMP-009, IMP-010, IMP-011, IMP-012, IMP-013

---

### Epic 14: Lightweight Critique-to-Evidence Ingestion Engine
- **Cadence Date:** 2026-11-08
- **Defensive Review (LL-###):** LL-045 (Pre-flight specification gate catching empty collection & None-safety gaps before contract drafting)
- **Positive Improvement Harvest:** IMP-015, IMP-016, IMP-017, IMP-018, IMP-019, IMP-020

---

### Epic 16: Deterministic Upper Confidence Bound (UCB) Decision Policy
- **Cadence Date:** 2026-11-08
- **Defensive Review (LL-###):** LL-046 (Continuous-Domain Widening in Statistical Bounds Must Be Guarded Against Classical Integer Reversion)
- **Positive Improvement Harvest:** IMP-021, IMP-022, IMP-023

---

### Epic 18: Pairwise Preference Optimization for Discrete Action Logits
- **Cadence Date:** 2026-11-08
- **Defensive Review (LL-###):** LL-047 (Enforce Explicit Numerical Tolerances and Non-Tautological Contract Assertions)
- **Positive Improvement Harvest:** IMP-024, IMP-025, IMP-026

---

### Epic 17: Scheduled Epsilon-Greedy Policy Baseline
- **Cadence Date:** 2026-11-08
- **Defensive Review (LL-###):** LL-048 (Dual Invocation Compatibility Patterns and Action Space Safety Mask Lock-In)
- **Positive Improvement Harvest:** IMP-027, IMP-028, IMP-029

---

### Epic 22: Scored-Search Decision Configuration Compilation
- **Cadence Date:** 2026-11-09
- **Defensive Review (LL-###):** LL-049 (A Review Line Outside the Triage Vocabulary Breaks Foreign Contracts After Merge), LL-050 (Approved Documents Can Name Code That Is Not There, and Criteria Edited After the Contract Trip the Baseline), LL-051 (PR Gate Stale Review Parsing and Confirmation Recognition), LL-052 (Pareto-Dominance Margin Collapse and Simplex Corner Collapse in Scored-Search Compilation)
- **Positive Improvement Harvest:** IMP-030, IMP-031, IMP-032, IMP-033, IMP-035, IMP-036

---

### Epic 38: Packaged Contextual Learning
- **Cadence Date:** 2026-11-09
- **Code & Methodology Recap:**
  - **Methodology:** Contextual bandit (catalog #4), a softmax policy over per-action weight rows applied to a caller-supplied feature vector, trained by REINFORCE with a baseline. ADR-038. The catalog still marks #4 `example_only` and HYP-AL-004 is still Testing; this recap changes neither (BRU-038-10).
  - **Code delivered:** `src/agent_learning_ext/learners/contextual_reinforce.py` (`ContextualReinforceLearner`, exported from `agent_learning_ext.learners` and `agent_learning_ext`); in `src/agent_learning_ext/cli.py` the flags `task-policy-init --feature-dim` and `task-policy-decide --features`, a `train` skip and an authority-set refusal for contextual snapshots. Contract tests: `tests/test_contextual_learner.py` and `tests/test_contextual_cli.py`.
  - **Design worth keeping:** one update rule for a batch: each action's row moves by the learning rate times the mean over used episodes of (R minus baseline) times (1 if chosen else 0, minus its probability) times the feature vector, with every episode scored on the weights the call started with; clipping and the version bump stay in `apply_update`. Seven skip counters in `extra`, one per unusable episode by first match, make a silent no-op visible. The learner reads `metadata["feature_vector"]` and never `context_features`. Every refusal path is tested by a before and after fingerprint of the store.
  - **Review findings by module:** 7 logged Q findings (3 accepted, 3 declined, 1 deferred), counted by `review_triage` from `Q-153-1` to `Q-159-1`. Learner: two accepted crash guards (an empty batch divided by zero; an episode with no `feature_vector` raised `KeyError`), two declined (a test-decay remark and a test path remark). CLI: one accepted hardening (a contextual snapshot with no `feature_dim` raised `KeyError`), one declined (a payload claim that did not crash), one deferred (`task-policy-authority-set` from full to low on a hand-made snapshot). Stories 38.2 and 38.3 had none. Both accepted learner findings were guards missing from the first story of the stack.
  - **Known gaps in the code:** no CLI path trains a contextual policy (IMP-037); the caller must copy the vector onto the episode (IMP-038); the `autonomy` block still reads the unused logits and the full-to-low authority-set case is unspecified (IMP-039).
  - **Where it could apply:** `escalate-diff-response`, using the Stage 16 measurements (change ratio, terms kept, downstream references) as features (IMP-041); `route-review-finding`, against the claim-type baseline of ADR-039 once Epic 39 is built (IMP-042). Both have very few real episodes today, so each is a shadow comparison, never authority.
  - **Demonstration:** demo 04 rewritten on `task-policy-init --feature-dim`, `decide --features` and the learner, with simulated rewards labelled synthetic, showing a policy that picks different actions in different contexts (IMP-040, extending IMP-023 and IMP-029).
  - **Evidence status:** the update rule is verified against hand-computed worked cases (a one-episode update, a two-episode batch mean, clipping) within 1e-9, and the contract fails when the advantage sign or the baseline update is changed. There is no evidence from real project data that a contextual policy does better than a plain softmax; HYP-AL-004 is unchanged.
- **Defensive Review (LL-###):** LL-053 (Approved documents named Microsoft-module placement again), LL-054 (Stacked story branches conflict in the log at every merge), LL-055 (A fresh worktree misses the dev and examples extras), LL-056 (Q findings repeat and re-anchor after a fix, and stacked stories ship latent crash paths)
- **Positive Improvement Harvest:** IMP-037, IMP-038, IMP-039, IMP-040, IMP-041, IMP-042, IMP-043, IMP-044

---

## 4. Phase Close Link (Stage 18)

All entries dispositioned `Rolled into Phase Next Intent Refinement` are harvested at Stage 18 into the next phase's Intent Refinement work.
