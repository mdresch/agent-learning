import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { cycleStartBlockers, effectiveStatus, epicCoverage, epicsInScope, gateSummary, loadConfig, loadStages, loadState, predecessorsCleared, recordOf, startBlocker, waiverFor } from "../lib/store.js";

export default defineTool({
  description:
    "Read the journey: effective status of each of the 18 stages in the current cycle, which stages may start now, pending approvals and gate counts. Call this first in every turn. This is a progress view, not proof of position: confirm against docs/project-docs/Project-Status-Register.md and gate episodes.",
  effect: "read",
  inputSchema: z.object({
    stageId: z.number().int().optional().describe("Return the full definition and record for one stage."),
  }),
  async execute({ stageId }) {
    const { stages } = loadStages();
    const config = loadConfig();
    const { state, warnings } = loadState();
    if (stageId !== undefined) {
      const s = stages.find((x) => x.id === stageId);
      if (!s) throw new Error(`Unknown stage ${stageId}`);
      return {
        definition: s,
        status: effectiveStatus(state, config, s),
        record: recordOf(state, s.id) ?? null,
        gates: gateSummary(state, s),
        openPredecessors: predecessorsCleared(state, config, stages, s),
        waiver: waiverFor(config, s.id) ?? null,
        epics: s.touchpoints.kind === "per_epic" ? epicCoverage(state, s, epicsInScope(config)) : null,
        approvals: state.approvals.filter((a) => a.stageId === s.id && a.cycle === state.cycle),
        warnings,
      };
    }
    const rows = stages.map((s) => {
      const status = effectiveStatus(state, config, s);
      const open = predecessorsCleared(state, config, stages, s);
      return {
        id: s.id,
        name: s.name,
        group: s.group,
        subagent: s.subagent,
        model: s.model ?? null,
        gateMode: s.gateMode,
        status,
        awaitingReadyToStart: startBlocker(state, s) !== undefined,
        canStart: startBlocker(state, s) === undefined && open.length === 0 && (status === "not_started" || status === "in_progress" || status === "changes_requested"),
        openPredecessors: open,
      };
    });
    const blockers = cycleStartBlockers(state, config, stages);
    const stage1 = stages.find((x) => x.startSignal);
    const waitingStart = stage1 ? startBlocker(state, stage1) : undefined;
    const released = state.startSignals.find((x) => x.cycle === state.cycle);
    return {
      cycle: state.cycle,
      readyToStart: waitingStart
        ? "WAITING. The human has not pressed Ready to start for stage 1 on the dashboard. Tell them and stop."
        : released
          ? `Released by ${released.decidedBy} at ${released.decidedAt}. Later stages start by themselves as each predecessor is approved.`
          : "Released by the phase start. Later stages start by themselves as each predecessor is approved.",
      phaseStarts: state.cycleStarts.map((c, i) => ({ cycle: i + 2, startedBy: c.decidedBy, at: c.decidedAt, note: c.note })),
      nextCycle: blockers.length === 0
        ? "Stages 17 and 18 are done. Tell the human they can start the next phase on the dashboard. You cannot start it."
        : `Not available. Stage(s) ${blockers.join(", ")} must be done first.`,
      profile: config.profile,
      stages: rows,
      pendingApprovals: state.approvals
        .filter((a) => a.status === "pending" && a.cycle === state.cycle)
        .map((a) => ({ id: a.id, stageId: a.stageId, taskId: a.taskId, artifact: a.artifact })),
      warnings,
    };
  },
});
