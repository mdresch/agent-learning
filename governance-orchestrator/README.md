# governance-orchestrator

One orchestrator agent and eight stage subagents that walk the 18-stage Intent-to-Outcome loop, report progress to a local dashboard, and stop at every gate for a human decision.

It generalizes two earlier agents:

| Earlier agent | Now lives in | What changed |
|---|---|---|
| `adr_reviewer` (coverage, pillars, researcher) | `stage-specification` | Same rubric, extended from ADRs to BRD, FDD and Stories. The three sub-roles are procedures inside one subagent, because subagents cannot nest. |
| `pr-reviewer` (`inspect_pr`, `submit_review`) | `stage-delivery` | Same complexity rubric. It recommends only; it cannot approve a PR or merge. |

## Shape

```
orchestrator ── journey_status / check_approvals   read progress and human decisions
     │          report_stage / request_approval     record reports, ask the human
     │          notify / write_document / run_command
     └─ task ─► stage-initiating (1 3 4 2)   stage-specification (5 6)   stage-baseline (7 8)
                stage-delivery (9 10)        stage-assurance (11 12 13)  stage-knowledge (14 15)
                stage-change-control (16 17) stage-closing (18)
```

Each subagent ends with a `STAGE_REPORT` block. The orchestrator is the only writer of journey state.

## Run it

```bash
cd governance-orchestrator
npm install
export GOVERNANCE_APPROVAL_SECRET="$(openssl rand -hex 24)"   # same value in both terminals
export GOVERNANCE_APPROVER="Menno Drescher"                    # optional

npm run dashboard          # terminal 1: http://127.0.0.1:4173
npx agent-sdk serve --dir . # terminal 2
```

Open the dashboard, then ask the orchestrator "Where are we in the governance loop?". Approval requests appear under **Needs you** with an optional desktop alert.

## Run it on Claude Code instead of Grok

The same orchestrator runs inside Claude Code with your Claude login, no model key and no Grok usage.

```bash
export GOVERNANCE_APPROVAL_SECRET="$(openssl rand -hex 24)"   # set in the shell before starting claude or the dashboard
cd governance-orchestrator && npm run dashboard                # terminal 1, uses ./.governance by default
cd .. && claude --agent governance-orchestrator                # terminal 2, from the repo root
```

The first time, Claude Code asks you to approve the project MCP server `governance` (from the repo's `.mcp.json`). If `GOVERNANCE_APPROVAL_SECRET` is not set when `claude` starts, that server is disabled and Claude Code warns; every other Claude Code session in this repo is unaffected.

| Piece | Where |
|---|---|
| Orchestrator and 8 stage subagents | `.claude/agents/*.md`, generated from `bot/` by `npm run build:claude` (check with `npm run check:claude`). Edit `bot/`, not the generated files |
| Tools | `mcp/server.ts`, a stdio MCP server that wraps the same `bot/tools/*.ts`, so the rules exist once |
| Server registration | `.mcp.json` at the repo root |

Least privilege is stricter here than on Grok: the orchestrator has no Bash or Edit and cannot write documents; stage subagents cannot report stages or file approvals; only subagents that draft documents get `write_document`; only those that need git or the policy CLI get `run_command`. The dashboard must use the same state folder as the MCP server (the default `.governance`, unless you set `GOVERNANCE_STATE_DIR` for both). Allow the read tools without prompts if you like, for example `mcp__governance__journey_status` and `mcp__governance__check_approvals` in `.claude/settings.local.json`.

Not yet exercised: a full live model turn on Claude Code. The server, the tool rules and the agent files were tested without a model.

## Guarantees and their limits

- The agent cannot approve. It has no `shell` or `edit`, and no tool writes `decisions.ndjson`. Decisions are HMAC-signed by the dashboard; unsigned lines are ignored.
- A policy stage cannot reach `done` without a human-approved approval for every gate. A missed gate is a recorded `gap`, never a backfill.
- `run_command` is a read-only allowlist. Recording the gate episode (`task-policy-adjudicate`, `task-episode-register`) remains a human action, so a dashboard approval is a sign-off signal and not the formal episode.
- Local only: the dashboard binds to 127.0.0.1. Anyone who can read the secret from your shell can forge a decision. `local.sandbox` is off because the agent's tools reach it over MCP, which a sandbox blocks.
- Stage 9 is a hand-off to the `implement-story` skill; the orchestrator never writes code.
- `journey/stages.json` is a copy of the chain table. `docs/intent-to-outcome-chain-coverage.md` wins on any difference.

## Approvals ahead, and one request per epic

The dashboard's **Approvals ahead** panel lists every decision the phase asks of you in authoring order, with what is done, waiting, in rework and still to come. Stages 6 and 8 take **one request per epic**: epic N is `docs/user-stories/epic-N-*.md` with its ADR, `BRD-N` and `FDD-N`, so you decide those documents together and each item keeps its own policy. These stages are done only when every in-scope epic is approved. Set `epicScope` in `journey/journey.config.json` to limit a phase to some epics; leave it out for all.

## Tailoring the journey

Edit `journey/journey.config.json` yourself. A waiver needs a reason, an approver and a date, and removes that stage from the path. It is not a way to backfill a missed gate. Per-stage requirements and gate lists are in `journey/stages.json`.

## Before you press Ready to start

Run `npm run preflight` from `governance-orchestrator/`. It uses no model. It checks the Claude CLI, `uv`, the approval secret, the agent files, that the tool server starts, that all 17 gate policies exist and what episodes each has, merge conflicts, uncommitted changes, leftover worktrees, each epic's ADR, BRD and FDD links, the phase scope, and whether the dashboard is up. Anything marked FAIL blocks a run. In the first run it found two unresolved merge conflicts and a broken link in epic 22.

## Skipping a review that already stands

Before it delegates a gate review, the orchestrator calls `check_reuse`. That tool decides in code, with no model call, whether an earlier accepted episode still stands. It does only when all four hold:

1. An accepted episode (disposition `accepted`, an `approve_*` action) names the document.
2. The document is unchanged since the commit that episode scored (`artifact_commit`). Only its Status row may differ, because recording an approval edits that row. `reuse.ignoreLinePatterns` in `journey.config.json` changes which lines are ignored.
3. The gate's TaskPolicy is the same one, by id and version.
4. The review criteria are unchanged: the stage's requirements, its gates and its subagent's instructions. The episode does not store them, so this is trust on first use: the first reuse records their hash, and any later edit to them forces a re-review.

When all four hold, no subagent runs, nothing is filed for you, and the dashboard and the orchestrator report the episode's results (id, date, robust utility, scored commit). When any fails, the normal review runs and you approve it, and the maintainer records the new episode. The agent can't create episodes, so reuse can only carry forward a decision a person already made. Only policy gates are reusable. On stages 6 and 8 an epic is skipped only if all four of its documents stand.

## Which model reviews what

`journey/stages.json` sets a `model` per stage and the orchestrator passes it when it delegates, so each request runs on the model it needs. These are my starting choices, not measured: change them in the file and run `npm run build:claude`.

| Model | Stages | Why |
|---|---|---|
| haiku | 8 Readiness, 10 Verification, 12 Outcome, 13 Observation | mostly commands and evidence, little judgment |
| sonnet | 1 to 7, 9, 11, 14, 15, 17, 18 and the orchestrator | reading and judging documents |
| opus | 16 Governance Change | classifying a diff against a frozen baseline is the highest-stakes call |

A subagent's own default is the strongest model any of its stages asks for, so a missed override is never too weak. `GOVERNANCE_MODEL` sets the model of a dashboard-launched orchestrator. Not yet checked live: that a per-request model override is honoured by Claude Code.

## Ready to start

Only stage 1 of each phase waits for you. The dashboard's **Ready to start** card holds an optional note and one button. Until you press it, every tool refuses to start, report on or file approvals for stage 1, and the orchestrator tells you it is waiting and stops. After that, each later stage starts by itself as soon as the stage before it is approved: the orchestrator confirms the gate episode, marks the stage done and moves on in the same turn, stopping only at a pending approval, a blocked stage or a gap. Starting the next phase releases its stage 1, so there is no second press. The card has an unticked box, "Also start the orchestrator now". Tick it and the dashboard runs `claude --agent governance-orchestrator` for you; leave it unticked and you run the orchestrator yourself.

### Launching from the dashboard uses your Claude usage

A launched run is a real Claude Code run on your login. In testing, a run that took one stage to its approval request cost about $0.15 to $0.20 in API terms. Nothing launches unless you tick the box on Ready to start or press **Continue**, and a run stops by itself at the first pending approval, blocked stage or gap, so you press Continue after you decide. Settings, set in the shell that starts the dashboard:

| Variable | Default | Meaning |
|---|---|---|
| `GOVERNANCE_RUN` | on | `off` removes launching entirely; the buttons then only record your decisions |
| `GOVERNANCE_RUN_BUDGET_USD` | 2 | a run that would spend more is stopped |
| `GOVERNANCE_RUN_TIMEOUT_MIN` | 20 | a run that takes longer is stopped |
| `GOVERNANCE_RUN_ALLOW_WRITES` | off | `1` lets stage subagents draft documents; off, a run can review but not write |

The prompts are fixed in `dashboard/server.mjs`, nothing the page sends becomes part of one, and the secret reaches the agent's tool server through the environment, never a file.

## Phases (cycles)

One cycle is one project phase. When stages 17 (Adaptation Plan) and 18 (Intent Refinement) are both done, the dashboard's **Next phase** card unlocks. You write your go decision, confirm, and Phase N+1 starts with all 18 stages empty and a new Spark. Phase N stays on record in `state.json` and the card lists each start. The agent can only tell you the card is open. Documents approved in an earlier phase remain frozen baselines and change through Stage 16.

## State

`.governance/` (git-ignored): `state.json` (agent), `decisions.ndjson` (dashboard: approvals and phase starts, signed), `events.ndjson` (audit trail). Override with `GOVERNANCE_STATE_DIR`.

## Not built yet

- Wiring a dashboard approval to `task-policy-adjudicate` and episode registration.
- Staleness: an upstream document changing after a downstream stage was approved does not mark the downstream stage for a re-check.
- Reopening an upstream stage on a reject. The subagent reports blocked and names it, and you decide.
- Reconciling `state.json` automatically from `Project-Status-Register.md` and gate episodes; today the orchestrator does it by reading them.
- Slack or email delivery of notifications (`bot/channels/`, `bot/schedules/`).
- Hosted deployment of the dashboard and agent.
