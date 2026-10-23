---
name: heal-contract-failure
description: Bounded, intent-first diagnosis and repair loop when a contract test breaks or a PR review exposes a contract defect in agent-learning.
---

# Skill: heal-contract-failure (agent-learning)

Generalized from two independently-converged real implementations. Unlike `implement-story`, almost nothing in the loop itself needed adaptation between the two source projects — this is discipline, not infrastructure. The one real thing that *does* vary per project is named below; confirm it before relying on this skill's own severity framing.

## Confirm first: does a mechanical enforcement layer exist here?

SocialEngage has one (a pre-commit hook backstopping contract-first discipline). ADPA, at the time this template was built, did not — every step below was discipline-only, with nothing to catch a skipped step mechanically. **This changes how load-bearing this skill is, not what it says**: with no hook, this skill's own discipline is the only thing standing in for one. Say explicitly, in this project's own copy of this file, which case applies.

## Dual Triggers: Mechanical Failure vs. PR Review Feedback ("Green Defect")

Contract failure is not limited to a red test runner in local validation or CI. It has two distinct triggers:

1. **Mechanical Test Failure (RED):** An existing assertion fails, a type-check breaks, or an unhandled exception halts execution.
2. **Review Feedback / Latent Defect (GREEN Defect):** A code reviewer (human or automated bot, e.g. Amazon Q) identifies a bug, crash risk, unhandled edge case, inverted assertion, or missing validation while existing contract tests are passing. 
   - *Core Rule:* A passing test suite with a latent defect is a **Contract Incompleteness Failure**.
   - *Anti-Pattern:* Never jump directly into implementation code to patch a review comment. Bypassing the contract violates contract-driven development just as severely as skipping Step 3 during initial implementation.

## Re-walk the whole chain, in order, every time — no classify-and-shortcut

1. **Re-validate Intent.** 
   - Re-open the failing contract's Intent header comment. Re-read the story and its Source ADR/BRD/FDD fresh, including any amendment since the contract was written.
   - *For PR Review:* Map the reviewer's finding back to the governing ADR/BRD/FDD. Is this finding enforcing an intended invariant, error-handling table entry, or domain boundary?
2. **Re-validate / Expose the Contract (Make it RED).**
   - Does the contract genuinely encode the story's *current* Acceptance Criteria? If stale, that needs a dated note and an explicit ADR reference, not a silent edit.
   - *For PR Review:* Before writing or touching any implementation fix, **encode the review finding as a failing test case or correct defective assertions** (e.g., correct inverted `pytest.approx` operands, pass malformed inputs to verify error exits, assert dropped criteria deltas). Run the test runner and verify it fails (RED).
3. **Re-validate the component `SKILL.md`.** 
   - Confirm governing ADRs/Stories, contract files, and constraints are still accurate.
   - *For PR Review:* If the review surfaced a new or clarified load-bearing constraint (e.g. `--retry-cap` must be $\ge 1$, criteria deltas must compute the union of before and after), document it immediately in `.claude/skills/<component>/SKILL.md`.
4. **Re-validate and, only now, fix the implementation (GREEN).** 
   - Minimal change to satisfy the now-failing, confirmed-correct contract test.
5. **Validate.** 
   - Run the specific contract (`uv run pytest tests/test_<x>.py`), then the full suite (`uv run pytest --ignore=tests/test_spark.py`).

**Hard stop, any step:** if getting to green requires weakening, skipping, or bypassing a contract's assertions or a lint rule, stop and escalate instead of forcing it through.

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

No mechanical enforcement layer: `.git/hooks` has no active hooks and no CI gate ties code changes to a contract. This skill's discipline is the only backstop. Contracts are pytest files under `tests/`; run one with `uv run pytest tests/test_<x>.py`, then the full suite with `uv run pytest --ignore=tests/test_spark.py`.
