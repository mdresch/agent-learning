import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import {
  epicsInScope,
  loadConfig,
  loadStages,
  loadState,
  logEvent,
  newId,
  notify,
  now,
  predecessorsCleared,
  recordOf,
  saveState,
  startBlocker,
  waiverFor,
} from "../lib/store.js";

export default defineTool({
  description:
    "Ask the human for a gate decision and raise a dashboard notification. This only files the request with your recommendation. It never approves anything: the human decides on the dashboard, and the registered approve-* policy is then recorded by the maintainer. Then stop and tell the human what is waiting. Stages 6 and 8 take ONE request per epic: pass epic and items (each item is one document with its own policy), and recommend approve only if every item passes. All other stages take taskId and artifact, one request per document.",
  effect: "write",
  dryRunResult: ({ stageId, taskId, epic }) => ({ filed: false, stageId, taskId, epic }),
  inputSchema: z.object({
    stageId: z.number().int(),
    taskId: z.string().optional().describe('A gate taskId of the stage, or "human-review" for human_review stages. Not used for epic requests.'),
    artifact: z.string().optional().describe("Repo-relative path of the artifact being judged. Not used for epic requests."),
    epic: z.string().optional().describe('Epic number, for example "12". Required on stages 6 and 8, rejected elsewhere.'),
    items: z
      .array(z.object({ taskId: z.string(), artifact: z.string(), artifactVersion: z.string().optional() }))
      .optional()
      .describe("The epic's documents: its ADR (approve-adr), BRD (approve-brd), FDD (approve-fdd) and stories file (approve-user-stories) on stage 6, or its stories file (validate-intent-foundation) on stage 8."),
    artifactVersion: z.string().optional().describe("Version, commit hash or content hash that was reviewed."),
    recommendation: z.enum(["approve", "reject", "request_revision"]),
    policyAction: z.string().optional().describe("The policy's own action name, for example approve_adr."),
    rationale: z.string().min(1).describe("The strongest reason, with the criteria results. For an epic, name any item that fails."),
    evidence: z.array(z.string()).default([]),
  }),
  async execute(input, ctx) {
    const { stages, defaultAgentId } = loadStages();
    const config = loadConfig();
    const { state } = loadState();
    const stage = stages.find((s) => s.id === input.stageId);
    if (!stage) throw new Error(`Unknown stage ${input.stageId}`);
    if (waiverFor(config, stage.id)) throw new Error(`Stage ${stage.id} is waived.`);
    const waiting = startBlocker(state, stage);
    if (waiting) throw new Error(waiting);
    const open = predecessorsCleared(state, config, stages, stage);
    if (open.length > 0) throw new Error(`Stage ${stage.id} is not open: stage(s) ${open.join(", ")} are not done or waived.`);

    const allowed = stage.gateMode === "human_review" ? ["human-review"] : stage.gates.map((g) => g.taskId);
    const perEpic = stage.touchpoints.kind === "per_epic";
    let taskId: string;
    let artifact: string;
    let items = input.items;

    if (perEpic) {
      if (!input.epic) throw new Error(`Stage ${stage.id} takes one request per epic: pass epic and items.`);
      const scope = epicsInScope(config);
      if (!scope.includes(input.epic)) throw new Error(`Epic ${input.epic} is not in this phase's scope. In scope: ${scope.join(", ") || "none found"}.`);
      if (!items || items.length === 0) throw new Error(`Epic ${input.epic}: list its documents in items.`);
      for (const it of items) {
        if (!allowed.includes(it.taskId)) throw new Error(`Stage ${stage.id} has no gate "${it.taskId}" (item ${it.artifact}). Allowed: ${allowed.join(", ")}.`);
      }
      taskId = `epic-${input.epic}`;
      artifact = `Epic ${input.epic}`;
    } else {
      if (input.epic || input.items) throw new Error(`Stage ${stage.id} does not batch by epic. Pass taskId and artifact, one request per document.`);
      if (!input.taskId || !input.artifact) throw new Error(`Stage ${stage.id} needs taskId and artifact.`);
      if (!allowed.includes(input.taskId)) {
        throw new Error(`Stage ${stage.id} has no gate "${input.taskId}". Allowed: ${allowed.join(", ") || "none (evidence stage)"}.`);
      }
      taskId = input.taskId;
      artifact = input.artifact;
      items = undefined;
    }

    const dup = state.approvals.find(
      (a) =>
        a.status === "pending" &&
        a.cycle === state.cycle &&
        a.stageId === stage.id &&
        (perEpic ? a.epic === input.epic : a.taskId === taskId && a.artifact === artifact),
    );
    if (dup) return { filed: false, reason: "already pending", approvalId: dup.id };

    const approval = {
      id: newId("apr"),
      cycle: state.cycle,
      stageId: stage.id,
      taskId,
      agentId: defaultAgentId,
      artifact,
      artifactVersion: input.artifactVersion,
      recommendation: input.recommendation,
      policyAction: input.policyAction,
      epic: perEpic ? input.epic : undefined,
      items,
      rationale: input.rationale,
      evidence: input.evidence,
      requestedAt: now(),
      status: "pending" as const,
    };
    state.approvals.push(approval);
    const rec = recordOf(state, stage.id);
    if (rec) rec.status = "ready_for_gate";
    notify(state, {
      level: "action",
      stageId: stage.id,
      approvalId: approval.id,
      message: perEpic
        ? `Approval needed: Epic ${input.epic}, ${items?.length ?? 0} document(s), stage ${stage.id}. Recommendation: ${input.recommendation}.`
        : `Approval needed: ${taskId} on ${artifact}. Recommendation: ${input.recommendation}.`,
    });
    saveState(state);
    logEvent("approval_requested", { approvalId: approval.id, stageId: stage.id, taskId, epic: input.epic, session: ctx.session.id });
    return { filed: true, approvalId: approval.id, next: "Stop. Tell the human an approval is waiting on the dashboard." };
  },
});
