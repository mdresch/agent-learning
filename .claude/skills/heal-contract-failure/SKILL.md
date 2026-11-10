---
name: heal-contract-failure
description: Bounded, intent-first diagnosis and repair loop when a contract test breaks or a PR review exposes a contract defect in agent-learning.
---

# Skill: heal-contract-failure (agent-learning)

Generalized from two independently-converged real implementations. Unlike `implement-story`, almost nothing in the loop itself needed adaptation between the two source projects — this is discipline, not infrastructure. The one real thing that *does* vary per project is named below; confirm it before relying on this skill's own severity framing.

## Confirm first: does a mechanical enforcement layer exist here?

SocialEngage has one (a pre-commit hook backstopping contract-first discipline). ADPA, at the time this template was built, did not — every step below was discipline-only, with nothing to catch a skipped step mechanically. **This changes how load-bearing this skill is, not what it says**: with no hook, this skill's own discipline is the only thing standing in for one. Say explicitly, in this project's own copy of this file, which case applies.

## Three Triggers: Mechanical Failure, PR Review Feedback ("Green Defect"), and Dependency Bump PRs

Contract failure is not limited to a red test runner in local validation or CI. There are three distinct triggers:

1. **Mechanical Test Failure (RED):** An existing assertion fails, a type-check breaks, or an unhandled exception halts execution.
2. **Review Feedback / Latent Defect (GREEN Defect):** A code reviewer (human or automated bot, e.g. Amazon Q) identifies a bug, crash risk, unhandled edge case, inverted assertion, or missing validation while existing contract tests are passing. 
   - *Core Rule:* A passing test suite with a latent defect is a **Contract Incompleteness Failure**.
   - *Anti-Pattern:* Never jump directly into implementation code to patch a review comment. Bypassing the contract violates contract-driven development just as severely as skipping Step 3 during initial implementation.
3. **Dependency Bump PR (e.g. Dependabot):** A bot opens a PR bumping a package version. The attached PR-check bots (for example the Cursor agents) report `NEUTRAL`, which is not a result of this project's contract suite, and "no regression visible" after a human applies the bump is not verification. **Procedure:** check out the bump PR's branch (or merge it into an isolated worktree), run the full accumulated contract suite against it, and only then merge it (GREEN) or walk the full heal loop below citing the dependency bump as the originating cause (RED). Never close a bump PR on "nothing looks broken" alone. (sidpa-template rule 34, rule 26.)

## Re-walk the whole chain, in order, every time — no classify-and-shortcut

1. **Re-validate Intent.** 
   - Re-open the failing contract's Intent header comment. Re-read the story and its Source ADR/BRD/FDD fresh, including any amendment since the contract was written.
   - *For PR Review:* Map the reviewer's finding back to the governing ADR/BRD/FDD. Is this finding enforcing an intended invariant, error-handling table entry, or domain boundary?
2. **Re-validate / Expose the Contract (Make it RED).**
   - Does the contract genuinely encode the story's *current* Acceptance Criteria? If stale, that needs a dated note and an explicit ADR reference, not a silent edit.
   - *For PR Review:* Before writing or touching any implementation fix, **encode the review finding as a failing test case or correct defective assertions** (e.g., correct inverted `pytest.approx` operands, pass malformed inputs to verify error exits, assert dropped criteria deltas). Run the test runner and verify it fails (RED). When the defect is already fixed or latent and no test can fail on the old code, obtain RED by breaking the behaviour under test, see the named test fail, restore, and check `git diff main -- src` is empty (LL-035).
3. **Re-validate the component `SKILL.md`.** 
   - Confirm governing ADRs/Stories, contract files, and constraints are still accurate.
   - *For PR Review:* If the review surfaced a new or clarified load-bearing constraint (e.g. `--retry-cap` must be $\ge 1$, criteria deltas must compute the union of before and after), document it immediately in `.claude/skills/<component>/SKILL.md`.
4. **Re-validate and, only now, fix the implementation (GREEN).** 
   - Minimal change to satisfy the now-failing, confirmed-correct contract test.
5. **Validate.** 
   - Run the specific contract (`uv run pytest tests/test_<x>.py`), then the full suite (plain `uv run pytest` after `uv sync --extra dev --extra examples`; a partial run is never called the whole suite, LL-013, LL-055).

**Hard stop, any step:** if getting to green requires weakening, skipping, or bypassing a contract's assertions or a lint rule, stop and escalate instead of forcing it through.

## Resuming a started `implement-story` run (branch or worktree already exists; LL-042)

An existing `feat/story-<X.Y>` branch or worktree means `implement-story` was started. Invoke this section only once abandonment is actually confirmed: ask the human when there is any ambiguity about whether another agent is still working it, because a quiet `git log` is not proof of abandonment and healing a live run is interference, not healing (sidpa-template rule 29). Once confirmed abandoned, the follow-up is this skill, not a second implementation. Inspect the leftovers read-only, then walk steps 1 to 5 from Intent: leftover tests and code are evidence to check against the ADR, BRD, FDD and story, not a contract to trust. Where the story has code, show the contract RED against the old code before the fix; where it has none, show the contract able to fail by mutating the production code it exercises (each mutation reverted, nothing committed), as in the Story 20.6 heal pass. Record the outcome as a dated correction entry in `implementation-log.md` if the original entry is already merged, naming the environment check (LL-033) and, for any review, the record shape (LL-034).

## Rules shared with `implement-story`

A heal pass runs the same loop, so these `implement-story` rules apply to it unchanged. They are named here and not repeated, so the two skills cannot drift apart (LL-007); read the step in `.claude/skills/implement-story/SKILL.md`.

- **Step 0:** worktree environment with `uv sync --all-extras` and a RED whose message names the story's symbol, not a missing package (LL-033); the story's approval records committed before the first code commit (LL-027); load this skill and re-read a step before doing it, record a missed step as a deviation (LL-028).
- **Step 1:** run a spec's worked example through the real gate function (LL-036).
- **Step 3:** observe RED by breaking the behaviour, see the named tests fail, restore, `git diff main -- src` empty (LL-035); no `hash(` in tests (LL-029); no `approx` on a container of tuples (LL-039).
- **Step 6:** `uvx <tool>` before skipping a gate with a missing tool (LL-030).
- **Step 8:** check a confirmation's claims against the head commit (LL-031); record a review with no findings as one prose bullet (LL-034); a stacked PR is unverified until it targets `main` and CI has run (LL-038).
- **Step 9:** read the unfiltered source before claiming an omission (LL-032).

## Bounded retries

Cap: 3 full walks of steps 1–5 per failure. Each attempt must differ from the last — a repeat with no new information from the previous failure is a signal to escalate early. Log each attempt (hypothesis, what changed, why it failed).

## Cross-epic regression (a foreign contract breaks)

Attribute before touching anything — check what the current story's diff actually changed against what the foreign contract exercises. Default remedy: narrow the current story's own change, not the previously-passing component. Track it as its own Intent and its own attempt budget, not a silent extension of the current one.

## Definition of "healed"

All of:
1. Steps 1–5 actually walked, not shortcut.
2. The originally failing check passes, OR for a PR review finding, a new contract test was observed RED and is now GREEN.
3. The full accumulated suite still passes.
4. Nothing weakened, skipped, or bypassed to get there.
5. Anything touched outside the story's declared scope is flagged, not silent.
6. Component `SKILL.md` and traceability are updated and accurate afterward.
7. Changes are committed to the PR branch citing the review feedback addressed.

## Feeding back to the template

If this skill's own re-walk ever surfaces a *pattern* worth generalizing — not just one story's fix, but a recurring shape of failure this loop keeps catching the same way — that belongs in this template's `docs/root-cause-log.md`, not just in the project's own `implementation-log.md`. The two logs serve different audiences: the project's log is "what happened here"; the template's log is "what does this teach the next project."

## Project facts (agent-learning)

No mechanical enforcement layer: `.git/hooks` has no active hooks and no CI gate ties code changes to a contract. This skill's discipline is the only backstop. Contracts are pytest files under `tests/`; run one with `uv run pytest tests/test_<x>.py`, then the full suite with plain `uv run pytest` (no `--ignore`; CI still excludes `tests/pmbok`, IMP-056, so a green CI is not the whole suite).
