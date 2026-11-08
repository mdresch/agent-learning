import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { loadState, logEvent, notify, saveState } from "../lib/store.js";

export default defineTool({
  description:
    "Post an informational or warning notification to the human's dashboard feed, for example a stage that was blocked, a tie-break halt, or a gate gap. Approval requests raise their own notification, so do not use this for those.",
  effect: "write",
  dryRunResult: ({ message }) => ({ posted: false, message }),
  inputSchema: z.object({
    level: z.enum(["info", "warn"]),
    message: z.string().min(1).max(500),
    stageId: z.number().int().optional(),
  }),
  async execute({ level, message, stageId }, ctx) {
    const { state } = loadState();
    notify(state, { level, message, stageId });
    saveState(state);
    logEvent("notification", { level, stageId, session: ctx.session.id });
    return { posted: true };
  },
});
