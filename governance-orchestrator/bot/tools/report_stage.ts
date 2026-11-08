import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import {
  effectiveStatus,
  epicCoverage,
  epicsInScope,
  gateSummary,
  latestPerKey,
  loadConfig,
  loadStages,
  loadState,
  logEvent,
  notify,
  predecessorsCleared,
  saveState,
  setRecord,
  startBlocker,
  waiverFor,
  now,
} from "../lib/store.js";

export default defineTool({
  description:
    "Record a stage subagent's report in the journey. Use the fields of its STAGE_REPORT block. A policy stage can reach done only after every gate has a human-approved approval; there is no way to mark a gate done without one, and a missed gate is recorded as gap, never backfilled.",
  effect: "write",
  dryRunResult: ({ stageId, status }) => ({ recorded: false, stageId, status }),
  inputSchema: z.object({
    stageId: z.number().int(),
    status: z.enum(["in_progress", "ready_for_gate", "changes_requested", "blocked", "gap", "done"]),
    summary: z.string().min(1).describe("Two or three sentences a human can read on the dashboard."),
    evidence: z.array(z.string()).default([]).describe("Commits, PRs, file paths with section, test runs, episode ids."),
    gaps: z.array(z.string()).default([]).describe("Open questions, unbuilt work, unmet requirements."),
    nextAction: z.string().default(""),
    reportedBy: z.string().describe("Subagent name."),
  }),
  async execute(input, ctx) {
    const { stages } = loadStages();
    const config = loadConfig();
    const { state } = loadState();
    const stage = stages.find((s) => s.id === input.stageId);
    if (!stage) throw new Error(`Unknown stage ${input.stageId}`);
    if (waiverFor(config, stage.id)) {
      throw new Error(`Stage ${stage.id} is waived in journey.config.json (${waiverFor(config, stage.id)?.reason}). Do not report on it.`);
    }

    const needsPredecessors = input.status !== "gap" && input.status !== "blocked";
    const waiting = startBlocker(state, stage);
    if (waiting && needsPredecessors) throw new Error(waiting);
    const open = predecessorsCleared(state, config, stages, stage);
    if (needsPredecessors && open.length > 0) {
      throw new Error(`Stage ${stage.id} cannot progress: stage(s) ${open.join(", ")} are not done or waived. Report a gap or blocked instead, or finish those first.`);
    }

    if (input.status === "done") {
      if (stage.gateMode === "policy" && stage.touchpoints.kind === "per_epic") {
        const epics = epicsInScope(config);
        if (epics.length === 0) throw new Error(`Stage ${stage.id} has no epics in scope (docs/user-stories/epic-N-*.md, narrowed by epicScope).`);
        const cov = epicCoverage(state, stage, epics);
        const left = [...cov.pending, ...cov.rework, ...cov.missing];
        if (left.length > 0) {
          throw new Error(
            `Stage ${stage.id} is not done: every in-scope epic needs a human-approved request. Not yet approved: ${left.map((e) => `epic ${e}`).join(", ")}${cov.pending.length ? ` (waiting on the human: ${cov.pending.join(", ")})` : ""}. Never backfill an approval.`,
          );
        }
      } else if (stage.gateMode === "policy") {
        const unmet = gateSummary(state, stage).filter((g) => g.approved === 0 || g.pending > 0);
        if (unmet.length > 0) {
          throw new Error(
            `Stage ${stage.id} is not done: gate(s) without a human approval or still pending: ${unmet.map((g) => g.taskId).join(", ")}. Call request_approval, then wait for the human. Never backfill an approval.`,
          );
        }
      }
      if (stage.gateMode === "pipeline" || stage.gateMode === "human_review") {
        // only the newest request per document counts: an older revise no longer blocks once it was re-requested and approved
        const blocked = latestPerKey(state.approvals.filter((a) => a.stageId === stage.id && a.cycle === state.cycle)).filter((a) => a.status !== "approved");
        if (blocked.length > 0) throw new Error(`Stage ${stage.id} has approvals that are not approved (${blocked.map((a) => `${a.id}:${a.status}`).join(", ")}).`);
        if (stage.gateMode === "human_review" && !state.approvals.some((a) => a.stageId === stage.id && a.cycle === state.cycle && a.status === "approved")) {
          throw new Error(`Stage ${stage.id} needs one human sign-off on its report. Call request_approval with taskId "human-review".`);
        }
      }
      if ((stage.gateMode === "evidence" || stage.gateMode === "pipeline") && input.evidence.length === 0) {
        throw new Error(`Stage ${stage.id} needs evidence references (commits, test runs, episode ids) to be done.`);
      }
    }

    setRecord(state, stage.id, {
      status: input.status,
      summary: input.summary,
      evidence: input.evidence,
      gaps: input.gaps,
      nextAction: input.nextAction,
      reportedBy: input.reportedBy,
      updatedAt: now(),
    });
    const level = input.status === "gap" || input.status === "blocked" ? "warn" : input.status === "ready_for_gate" ? "action" : "info";
    notify(state, { level, stageId: stage.id, message: `Stage ${stage.id} ${stage.name}: ${input.status}. ${input.summary}` });
    saveState(state);
    logEvent("stage_reported", { stageId: stage.id, status: input.status, reportedBy: input.reportedBy, session: ctx.session.id });
    return { recorded: true, stageId: stage.id, effectiveStatus: effectiveStatus(state, config, stage) };
  },
});
