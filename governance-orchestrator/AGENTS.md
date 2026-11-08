# governance-orchestrator

Agent SDK project (`@grok/agent-sdk`). This file is for coding agents editing the project. The served agent's prompt is `bot/instructions.md`. Operator guide: `README.md`.

## Loop

```bash
npm install
npm run check
agent-sdk validate --dir .
agent-sdk info --dir . --json
agent-sdk eval --dir .
```

Run the CLI under Node, never Bun. Set `GOVERNANCE_APPROVAL_SECRET` (same value for the agent server and `npm run dashboard`) and point `GOVERNANCE_STATE_DIR` at a scratch folder for evals.

## Layout

- `journey/stages.json` is the stage registry. It mirrors `docs/intent-to-outcome-chain-coverage.md`; if they differ, that document wins.
- `journey/journey.config.json` is the human's tailoring. No agent tool writes `journey/`.
- `bot/instructions.md` is the orchestrator prompt. Keep it short; stage detail lives in `bot/subagents/<stage-group>/instructions.md`.
- `bot/lib/store.ts` owns state. `state.json` is written only by tools; `decisions.ndjson` is written only by `dashboard/server.mjs` and is HMAC-signed.
- `bot/tools/` one tool per file. Subagents inherit these; they cannot have their own.
- `dashboard/` is the human's view. It uses `textContent` only, because stage reports are agent-written.

## Invariants — do not break

1. The agent never approves. There is no tool that writes a decision, and `bot/agent.ts` has no `shell` or `edit`. Do not add either.
2. `report_stage` cannot mark a policy stage done without a human-approved approval per gate. Do not add a bypass or a backfill.
3. `run_command` stays an allowlist. Gate adjudication (`task-policy-adjudicate`), episode registration, commit, push and merge stay human actions.
4. `write_document` refuses generated documents and frozen (approved) baselines.
5. Subagents report; only the orchestrator calls `report_stage`.
6. Only the human starts a cycle (one cycle is one phase), through the dashboard, and only when stages 17 and 18 are both done. The start is a signed `cycle_start` line in `decisions.ndjson`; the cycle number is derived from those lines on every load, and stage records are keyed `<cycle>:<stageId>`. No tool may start or reset a cycle.
7. Only stage 1 waits for a human start (`startSignal: true` in `journey/stages.json`). It is a signed `stage_start` line from the dashboard, tied to its cycle, and `report_stage` and `request_approval` refuse stage 1 without it (a `gap` or `blocked` report is still allowed). Do not add a start signal to any later stage: they start by themselves when their predecessors are done.

8. An earlier episode is reused only through `check_reuse` (`bot/lib/reuse.ts`): accepted episode, document unchanged since its scored commit, same policy, unchanged review criteria. Never reuse by the model's own reasoning, never let a tool create or edit an episode, and keep it limited to policy gates.

## Two hosts, one source

`bot/` is the source of truth. `mcp/server.ts` exposes `bot/tools/*.ts` to Claude Code, and `scripts/build-claude-agents.mjs` generates `../.claude/agents/*.md` from `bot/instructions.md` and `bot/subagents/*`. After changing any prompt, run `npm run build:claude`; `npm run check:claude` fails if they drifted. A new subagent needs an entry in `SUBAGENT_TOOLS` in the generator. Never edit the generated files.

## Do not

- Grow host TypeScript for classification or reply composition. That stays in instructions. Host code owns state, signatures, allowlists and side-effect gates.
- Point `serve` at a parent folder. It mounts every sibling agent.
- Hand-write generated plans from here. Stage 7 only checks and requests.
