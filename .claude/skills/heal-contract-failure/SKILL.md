# Skill: heal-contract-failure (agent-learning)

Generalized from two independently-converged real implementations. Unlike `implement-story`, almost nothing in the loop itself needed adaptation between the two source projects — this is discipline, not infrastructure. The one real thing that *does* vary per project is named below; confirm it before relying on this skill's own severity framing.

## Confirm first: does a mechanical enforcement layer exist here?

SocialEngage has one (a pre-commit hook backstopping contract-first discipline). ADPA, at the time this template was built, did not — every step below was discipline-only, with nothing to catch a skipped step mechanically. **This changes how load-bearing this skill is, not what it says**: with no hook, this skill's own discipline is the only thing standing in for one. Say explicitly, in this project's own copy of this file, which case applies.

## Re-walk the whole chain, in order, every time — no classify-and-shortcut

1. **Re-validate Intent.** Re-open the failing contract's Intent header comment. Re-read the story and its Source ADR fresh, including any amendment since the contract was written.
2. **Re-validate the Contract.** Does it genuinely encode the story's *current* Acceptance Criteria? If stale, that needs a dated note and an explicit ADR reference, not a silent edit.
3. **Re-validate the component `SKILL.md`.** Confirm governing ADRs/Stories, contract files, and constraints are still accurate. Fix directly if drifted — this one's documentation, not a behavior guarantee.
4. **Re-validate and, only now, fix the implementation.** Minimal change to satisfy the now-confirmed-correct contract.
5. **Validate.** Run the specific contract, then the epic's suite.

**Hard stop, any step:** if getting to green requires weakening, skipping, or bypassing a contract's assertions or a lint rule, stop and escalate instead of forcing it through.

## Bounded retries

Cap: 3 full walks of steps 1–5 per failure. Each attempt must differ from the last — a repeat with no new information from the previous failure is a signal to escalate early. Log each attempt (hypothesis, what changed, why it failed).

## Cross-epic regression (a foreign contract breaks)

Attribute before touching anything — check what the current story's diff actually changed against what the foreign contract exercises. Default remedy: narrow the current story's own change, not the previously-passing component. Track it as its own Intent and its own attempt budget, not a silent extension of the current one.

## Definition of "healed"

All of: steps 1–5 actually walked, not shortcut; the originally failing check passes; the full accumulated suite still passes; nothing weakened/skipped/bypassed to get there; anything touched outside the story's declared scope is flagged, not silent; `SKILL.md` and traceability are accurate afterward.

## Feeding back to the template

If this skill's own re-walk ever surfaces a *pattern* worth generalizing — not just one story's fix, but a recurring shape of failure this loop keeps catching the same way — that belongs in this template's `docs/root-cause-log.md`, not just in the project's own `implementation-log.md`. The two logs serve different audiences: the project's log is "what happened here"; the template's log is "what does this teach the next project."

## Project facts (agent-learning)

No mechanical enforcement layer: `.git/hooks` has no active hooks and no CI gate ties code changes to a contract. This skill's discipline is the only backstop. Contracts are pytest files under `tests/`; run one with `.venv/Scripts/python -m pytest tests/test_<x>.py`, then the full `tests/` suite.
