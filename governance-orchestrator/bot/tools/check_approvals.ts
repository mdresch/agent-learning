import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { loadState } from "../lib/store.js";

export default defineTool({
  description:
    "Read human decisions on approval requests (verified against the dashboard's signature). Use at the start of a turn to see what the human decided, then act: approved means call report_stage done once the policy episode is recorded; revise or rejected means send the stage back to its subagent with the human's note.",
  effect: "read",
  inputSchema: z.object({
    stageId: z.number().int().optional(),
    status: z.enum(["pending", "approved", "rejected", "revise", "waived"]).optional(),
  }),
  async execute({ stageId, status }) {
    const { state, warnings } = loadState();
    const rows = state.approvals
      .filter((a) => a.cycle === state.cycle)
      .filter((a) => stageId === undefined || a.stageId === stageId)
      .filter((a) => status === undefined || a.status === status)
      .map((a) => ({
        id: a.id,
        stageId: a.stageId,
        taskId: a.taskId,
        artifact: a.artifact,
        epic: a.epic ?? null,
        items: a.items ?? null,
        artifactVersion: a.artifactVersion ?? null,
        recommendation: a.recommendation,
        status: a.status,
        decidedBy: a.decidedBy ?? null,
        decidedAt: a.decidedAt ?? null,
        humanNote: a.note ?? null,
      }));
    return { approvals: rows, warnings };
  },
});
