import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { DEFAULT_IGNORE, classifyDiff, parseJsonArray, pickEpisode, policyMatches, reviewBasisHash, run, toEpisodeFacts, type EpisodeFacts } from "../lib/reuse.js";
import {
  epicsInScope,
  latestPerKey,
  loadConfig,
  loadStages,
  loadState,
  logEvent,
  newId,
  notify,
  now,
  predecessorsCleared,
  saveState,
  startBlocker,
  waiverFor,
  type Approval,
} from "../lib/store.js";

type ItemVerdict = {
  taskId: string;
  artifact: string;
  verdict: "reuse" | "review";
  reason: string;
  episode?: { id: string; acceptedAt: string; robustUtility: number | null; expectedUtility: number | null; policyVersion: number | null; scoredAtCommit: string | null; resultSummary: string };
};

export default defineTool({
  description:
    "Before you delegate a review, ask whether an earlier accepted gate episode still stands for these documents. Reuse needs ALL of: an accepted episode that names the document; the document unchanged since the commit that episode scored (only its Status row may differ); the same gate policy (id and version); and unchanged review criteria. If every item passes, the earlier approval is carried forward and no model call or new approval is needed: mention the episode's results to the human. If any item fails, the result says why, and you run the normal review for those items, which ends in a human approval and a new episode. Pass epic on stages 6 and 8. Only policy gates can be reused.",
  effect: "write",
  dryRunResult: ({ stageId }) => ({ reused: false, stageId }),
  inputSchema: z.object({
    stageId: z.number().int(),
    epic: z.string().optional().describe("Epic number. Required on stages 6 and 8, rejected elsewhere."),
    items: z.array(z.object({ taskId: z.string(), artifact: z.string() })).min(1).describe("Each document and the gate it falls under."),
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
    if (stage.gateMode !== "policy") throw new Error(`Stage ${stage.id} has no policy gate, so there is no episode to reuse.`);

    const perEpic = stage.touchpoints.kind === "per_epic";
    if (perEpic) {
      if (!input.epic) throw new Error(`Stage ${stage.id} takes one request per epic: pass epic.`);
      if (!epicsInScope(config).includes(input.epic)) throw new Error(`Epic ${input.epic} is not in this phase's scope.`);
    } else if (input.epic) {
      throw new Error(`Stage ${stage.id} does not batch by epic.`);
    }
    const allowed = stage.gates.map((g) => g.taskId);
    for (const it of input.items) if (!allowed.includes(it.taskId)) throw new Error(`Stage ${stage.id} has no gate "${it.taskId}". Allowed: ${allowed.join(", ")}.`);

    // Already approved or already waiting for the human: nothing to reuse.
    const mine = latestPerKey(state.approvals.filter((a) => a.stageId === stage.id && a.cycle === state.cycle));
    const existing = mine.find((a) => (perEpic ? a.epic === input.epic : input.items.some((i) => a.taskId === i.taskId && a.artifact === i.artifact)));
    if (existing?.status === "pending") return { reused: false, reason: "A request is already waiting for the human.", approvalId: existing.id };
    if (existing?.status === "approved") return { reused: true, already: true, approvalId: existing.id, reason: "Already approved in this phase." };

    const ignore = (config.reuse?.ignoreLinePatterns ?? DEFAULT_IGNORE).map((p) => new RegExp(p));
    const basis = reviewBasisHash(stage);
    state.reuseLedger ??= {};
    const episodeCache = new Map<string, EpisodeFacts[]>();
    const policyCache = new Map<string, { id: string; version: number } | null>();
    const verdicts: ItemVerdict[] = [];
    const pendingLedger: Record<string, string> = {};

    for (const it of input.items) {
      const review = (reason: string): ItemVerdict => ({ taskId: it.taskId, artifact: it.artifact, verdict: "review", reason });

      if (!episodeCache.has(it.taskId)) {
        const r = await run("uv", ["run", "agent-learn", "task-episodes-list", defaultAgentId, "--task-id", it.taskId, "--limit", "50"]);
        let eps: EpisodeFacts[] = [];
        try { eps = parseJsonArray(r.stdout).map(toEpisodeFacts).filter((e): e is EpisodeFacts => e !== undefined); } catch { /* treated as none */ }
        episodeCache.set(it.taskId, eps);
      }
      const ep = pickEpisode(episodeCache.get(it.taskId) ?? [], it.artifact);
      if (!ep) { verdicts.push(review(`No accepted ${it.taskId} episode names ${it.artifact}.`)); continue; }
      const facts = { id: ep.id, acceptedAt: ep.createdAt, robustUtility: ep.robustUtility, expectedUtility: ep.expectedUtility, policyVersion: ep.policyVersion, scoredAtCommit: ep.artifactCommit, resultSummary: ep.resultSummary };

      if (!ep.artifactCommit) { verdicts.push({ ...review(`Episode ${ep.id} records no artifact commit, so unchanged cannot be shown.`), episode: facts }); continue; }
      const diff = await run("git", ["diff", "--unified=0", ep.artifactCommit, "--", it.artifact]);
      if (diff.code !== 0) { verdicts.push({ ...review(`Could not compare with commit ${ep.artifactCommit}: ${diff.stderr.trim().slice(0, 120)}`), episode: facts }); continue; }
      const { changed } = classifyDiff(diff.stdout, ignore);
      if (changed.length > 0) {
        verdicts.push({ ...review(`The document changed since commit ${ep.artifactCommit} (${changed.length} line(s), first: ${changed[0]}).`), episode: facts });
        continue;
      }

      if (!policyCache.has(it.taskId)) {
        const r = await run("uv", ["run", "agent-learn", "task-policy", "--agent-id", defaultAgentId, "--task-id", it.taskId]);
        let cur: { id: string; version: number } | null = null;
        try { const p = JSON.parse(r.stdout.slice(r.stdout.indexOf("{"))).current_policy; if (p?.id) cur = { id: String(p.id), version: Number(p.version) }; } catch { /* null */ }
        policyCache.set(it.taskId, cur);
      }
      const cur = policyCache.get(it.taskId);
      if (!cur) { verdicts.push({ ...review(`Could not read the current ${it.taskId} policy.`), episode: facts }); continue; }
      if (!policyMatches(ep, cur)) { verdicts.push({ ...review(`The ${it.taskId} policy changed (episode: ${ep.policyId} v${ep.policyVersion}, now ${cur.id} v${cur.version}).`), episode: facts }); continue; }

      const ledgerKey = `${stage.id}|${it.taskId}|${it.artifact}|${ep.id}`;
      const seen = state.reuseLedger[ledgerKey];
      if (seen && seen.basis !== basis) { verdicts.push({ ...review("The review criteria changed since this episode was last reused."), episode: facts }); continue; }
      if (!seen) pendingLedger[ledgerKey] = basis;
      verdicts.push({ taskId: it.taskId, artifact: it.artifact, verdict: "reuse", reason: `Accepted ${ep.createdAt.slice(0, 10)}; document unchanged since ${ep.artifactCommit} apart from its Status row; policy v${cur.version} unchanged.`, episode: facts });
    }

    if (verdicts.some((v) => v.verdict === "review")) {
      return { reused: false, items: verdicts, next: "Run the normal review for the items marked review. For items marked reuse, cite their episode in the rationale instead of re-reviewing them." };
    }

    // Every item stands. Carry the earlier approval forward.
    const at = now();
    const episodeIds = [...new Set(verdicts.map((v) => v.episode!.id))];
    const lines = verdicts.map((v) => `${v.taskId} on ${v.artifact}: episode ${v.episode!.id}, accepted ${v.episode!.acceptedAt.slice(0, 10)}, robust utility ${v.episode!.robustUtility?.toFixed(3) ?? "n/a"}`);
    const summary = `Reused earlier accepted episode(s) ${episodeIds.join(", ")}. No new review or approval was needed.`;
    const base = { cycle: state.cycle, stageId: stage.id, agentId: defaultAgentId, recommendation: "approve" as const, requestedAt: at, status: "pending" as const, reuse: { episodeIds, summary, recordedAt: at } };
    const created: Approval[] = perEpic
      ? [{ ...base, id: newId("apr"), taskId: `epic-${input.epic}`, artifact: `Epic ${input.epic}`, epic: input.epic, items: input.items, rationale: summary, evidence: lines }]
      : input.items.map((it) => ({ ...base, id: newId("apr"), taskId: it.taskId, artifact: it.artifact, rationale: summary, evidence: lines.filter((l) => l.includes(it.artifact)) }));
    state.approvals.push(...created);
    for (const [k, v] of Object.entries(pendingLedger)) state.reuseLedger[k] = { basis: v, at };
    notify(state, { level: "info", stageId: stage.id, message: `Stage ${stage.id}: reused ${lines.join("; ")}. Documents unchanged since they were scored and the policy is the same, so no re-approval is needed.` });
    saveState(state);
    logEvent("episode_reused", { stageId: stage.id, episodes: episodeIds, session: ctx.session.id });
    return { reused: true, approvalIds: created.map((a) => a.id), episodes: verdicts.map((v) => v.episode), mention: lines, next: "Tell the human these results. Skip the review and file nothing for approval. Mark the stage done when every gate is covered." };
  },
});
