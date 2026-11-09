// Journey state for the governance orchestrator.
//
// Two writers, two files, so neither can forge the other's data:
//   state.json       written only by the agent's tools (stage reports, approval requests, notifications)
//   decisions.ndjson written only by dashboard/server.mjs, one HMAC-signed line per human decision
// A decision counts only when its signature verifies against GOVERNANCE_APPROVAL_SECRET.
// The agent has no shell and no edit tool, and the secret lives in the environment only.

import { createHmac, randomUUID, timingSafeEqual } from "node:crypto";
import { appendFileSync, existsSync, mkdirSync, readFileSync, readdirSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
export const projectRoot = resolve(here, "..", "..");
export const repoRoot = resolve(projectRoot, "..");
export const stateDir = process.env.GOVERNANCE_STATE_DIR ?? join(projectRoot, ".governance");

export type GateMode = "policy" | "pipeline" | "evidence" | "human_review";
export type StageStatus =
  | "not_started"
  | "in_progress"
  | "ready_for_gate"
  | "awaiting_approval"
  | "changes_requested"
  | "blocked"
  | "gap"
  | "done"
  | "waived";
export type ApprovalStatus = "pending" | "approved" | "rejected" | "revise" | "waived";
export type DecisionValue = Exclude<ApprovalStatus, "pending">;

export type Gate = {
  taskId: string;
  authority: "full" | "low";
}
export type Touchpoint =
  | { kind: "fixed"; count: number; label: string }
  | { kind: "variable"; minimum: number; label: string }
  | { kind: "per_epic"; label: string }
  | { kind: "external"; label: string }
  | { kind: "none"; label: string };
// One request per epic bundles that epic's documents; each item still names its own policy.
export type ApprovalItem = {
  taskId: string;
  artifact: string;
  artifactVersion?: string;
}
export type StageDef = {
  id: number;
  key: string;
  name: string;
  group: string;
  pmbok: string;
  subagent: string;
  after: number[];
  gateMode: GateMode;
  gates: Gate[];
  artifacts: string[];
  writes: string[];
  requirements: string[];
  touchpoints: Touchpoint;
  startSignal?: boolean; // waits for the human's Ready to start, once per phase (stage 1 only)
  model?: string; // model for this stage's review: haiku, sonnet, opus or fable. The orchestrator passes it when it delegates
  note?: string;
}
export type StageRecord = {
  status: StageStatus;
  summary: string;
  evidence: string[];
  gaps: string[];
  nextAction: string;
  reportedBy: string;
  updatedAt: string;
}
export type Approval = {
  id: string;
  cycle: number;
  stageId: number;
  taskId: string;
  agentId: string;
  artifact: string;
  artifactVersion?: string;
  recommendation: "approve" | "reject" | "request_revision";
  policyAction?: string;
  // Set when an earlier accepted gate episode still stands (see lib/reuse.ts). Such an approval counts as approved
  // without a new human decision, because a human already made that decision and nothing it rested on has changed.
  reuse?: { episodeIds: string[]; summary: string; recordedAt: string };
  epic?: string; // set on stages whose touchpoints are per_epic (6 and 8)
  items?: ApprovalItem[]; // the documents the epic request covers
  rationale: string;
  evidence: string[];
  requestedAt: string;
  status: ApprovalStatus;
  decidedBy?: string;
  decidedAt?: string;
  note?: string;
}
export type Notification = {
  id: string;
  at: string;
  level: "info" | "action" | "warn";
  stageId?: number;
  approvalId?: string;
  message: string;
}
// A cycle is one project phase. The human starts the next one from the dashboard, only when stages 17 and 18
// are both done. The start is a signed line in decisions.ndjson, so the cycle number is derived on every load:
// cycle = 1 + the number of verified cycle starts. Stage records are keyed "<cycle>:<stageId>".
export type CycleStart = {
  note: string;
  decidedBy: string;
  decidedAt: string;
}
// The human's "Ready to start" for stage 1 of a phase. Signed, so the cycle it belongs to is part of the signature.
export type StartSignal = {
  cycle: number;
  note: string;
  decidedBy: string;
  decidedAt: string;
}
export type JourneyState = {
  version: 1;
  cycle: number; // derived on load; the stored value is informational
  cycleStarts: CycleStart[]; // derived on load, never stored
  startSignals: StartSignal[]; // derived on load, never stored
  reuseLedger?: Record<string, { basis: string; at: string }>; // review criteria hash when an episode was first reused
  updatedAt: string;
  stages: Record<string, StageRecord>;
  approvals: Approval[];
  notifications: Notification[];
}
export type JourneyConfig = {
  profile: string;
  cycle: number;
  approver: string;
  epicScope?: string[]; // epic numbers in this phase; omit for every epic found in docs/user-stories
  reuse?: { ignoreLinePatterns?: string[] }; // lines whose change does not count as a document change
  stageOverrides: Record<string, { applicable?: boolean; waiver?: { reason: string; approvedBy: string; date: string } }>;
}
type DecisionLine = {
  approvalId: string;
  decision: DecisionValue;
  note: string;
  decidedBy: string;
  decidedAt: string;
  sig: string;
}
type CycleLine = {
  type: "cycle_start";
  note: string;
  decidedBy: string;
  decidedAt: string;
  sig: string;
}
type StartLine = {
  type: "stage_start";
  stageId: number;
  cycle: number;
  note: string;
  decidedBy: string;
  decidedAt: string;
  sig: string;
}

export function loadStages(): { defaultAgentId: string; stages: StageDef[] } {
  const raw = JSON.parse(readFileSync(join(projectRoot, "journey", "stages.json"), "utf8"));
  return { defaultAgentId: raw.defaultAgentId as string, stages: raw.stages as StageDef[] };
}

export function loadConfig(): JourneyConfig {
  return JSON.parse(readFileSync(join(projectRoot, "journey", "journey.config.json"), "utf8")) as JourneyConfig;
}

export function waiverFor(config: JourneyConfig, stageId: number) {
  const o = config.stageOverrides[String(stageId)];
  if (o?.applicable === false && o.waiver?.reason && o.waiver.approvedBy && o.waiver.date) return o.waiver;
  return undefined;
}

export const now = () => new Date().toISOString();
export const newId = (prefix: string) => `${prefix}-${randomUUID().slice(0, 8)}`;

function emptyState(cycle: number): JourneyState {
  return { version: 1, cycle, cycleStarts: [], startSignals: [], updatedAt: now(), stages: {}, approvals: [], notifications: [] };
}

function statePath() {
  return join(stateDir, "state.json");
}

/** Signature over a decision. Shared algorithm with dashboard/server.mjs. */
export function signDecision(secret: string, d: Omit<DecisionLine, "sig">): string {
  return createHmac("sha256", secret)
    .update(JSON.stringify([d.approvalId, d.decision, d.note, d.decidedBy, d.decidedAt]))
    .digest("hex");
}

/** Signature over a cycle start. Shared algorithm with dashboard/server.mjs. */
export function signCycle(secret: string, d: Omit<CycleLine, "sig">): string {
  return createHmac("sha256", secret).update(JSON.stringify(["cycle_start", d.note, d.decidedBy, d.decidedAt])).digest("hex");
}

function sameSig(expectedHex: string, actual: unknown) {
  const expected = Buffer.from(expectedHex, "hex");
  const got = Buffer.from(String(actual), "hex");
  return expected.length === got.length && timingSafeEqual(expected, got);
}

/** Signature over a stage-1 Ready to start. Shared algorithm with dashboard/server.mjs. */
export function signStart(secret: string, d: Omit<StartLine, "sig">): string {
  return createHmac("sha256", secret).update(JSON.stringify(["stage_start", d.stageId, d.cycle, d.note, d.decidedBy, d.decidedAt])).digest("hex");
}

function verifiedDecisions(): { lines: DecisionLine[]; starts: CycleStart[]; signals: StartSignal[]; secretMissing: boolean; rejected: number } {
  const secret = process.env.GOVERNANCE_APPROVAL_SECRET;
  const file = join(stateDir, "decisions.ndjson");
  if (!existsSync(file)) return { lines: [], starts: [], signals: [], secretMissing: !secret, rejected: 0 };
  if (!secret) return { lines: [], starts: [], signals: [], secretMissing: true, rejected: 0 };
  const lines: DecisionLine[] = [];
  const starts: CycleStart[] = [];
  const signals: StartSignal[] = [];
  let rejected = 0;
  for (const raw of readFileSync(file, "utf8").split("\n")) {
    if (!raw.trim()) continue;
    try {
      const d = JSON.parse(raw) as DecisionLine | CycleLine | StartLine;
      if ("type" in d && d.type === "cycle_start") {
        if (sameSig(signCycle(secret, d), d.sig)) starts.push({ note: d.note, decidedBy: d.decidedBy, decidedAt: d.decidedAt });
        else rejected++;
      } else if ("type" in d && d.type === "stage_start") {
        if (d.stageId === 1 && sameSig(signStart(secret, d), d.sig)) signals.push({ cycle: d.cycle, note: d.note, decidedBy: d.decidedBy, decidedAt: d.decidedAt });
        else rejected++;
      } else if ("approvalId" in d) {
        if (sameSig(signDecision(secret, d), d.sig)) lines.push(d);
        else rejected++;
      } else {
        rejected++;
      }
    } catch {
      rejected++;
    }
  }
  starts.sort((a, b) => a.decidedAt.localeCompare(b.decidedAt));
  return { lines, starts, signals, secretMissing: false, rejected };
}

/** state.json plus verified human decisions. The first verified decision for an approval is final. */
export function loadState(): { state: JourneyState; warnings: string[] } {
  const config = loadConfig();
  const warnings: string[] = [];
  let state: JourneyState;
  if (existsSync(statePath())) {
    state = JSON.parse(readFileSync(statePath(), "utf8")) as JourneyState;
  } else {
    state = emptyState(config.cycle);
  }
  const { lines, starts, signals, secretMissing, rejected } = verifiedDecisions();
  state.cycleStarts = starts;
  state.startSignals = signals;
  state.cycle = 1 + starts.length;
  if (secretMissing) warnings.push("GOVERNANCE_APPROVAL_SECRET is not set: human decisions cannot be verified and are ignored.");
  if (rejected > 0) warnings.push(`${rejected} decision line(s) failed signature verification and were ignored.`);
  for (const a of state.approvals) {
    if (a.reuse) {
      a.status = "approved";
      a.decidedBy = "reused episode";
      a.decidedAt = a.reuse.recordedAt;
      a.note = a.reuse.summary;
      continue;
    }
    if (a.status !== "pending") continue;
    const d = lines.find((l) => l.approvalId === a.id);
    if (d) {
      a.status = d.decision;
      a.decidedBy = d.decidedBy;
      a.decidedAt = d.decidedAt;
      a.note = d.note;
    }
  }
  return { state, warnings };
}

/** Persist agent-owned state. Decision overlays are never written back: they stay derived. */
export function saveState(state: JourneyState) {
  mkdirSync(stateDir, { recursive: true });
  const { cycleStarts: _derived, startSignals: _derivedSignals, ...persisted } = state;
  const stored = {
    ...persisted,
    updatedAt: now(),
    // keep requested status; decisions are re-derived from decisions.ndjson on every load (reused episodes remain approved)
    approvals: state.approvals.map((a) => {
      if (a.reuse) {
        return {
          ...a,
          status: "approved",
          decidedBy: "reused episode",
          decidedAt: a.reuse.recordedAt,
          note: a.reuse.summary,
        };
      }
      return { ...a, status: "pending", decidedBy: undefined, decidedAt: undefined, note: undefined };
    }),
  };
  const tmp = `${statePath()}.tmp`;
  writeFileSync(tmp, JSON.stringify(stored, null, 2));
  renameSync(tmp, statePath());
}

export function logEvent(type: string, data: Record<string, unknown>) {
  mkdirSync(stateDir, { recursive: true });
  appendFileSync(join(stateDir, "events.ndjson"), JSON.stringify({ at: now(), type, ...data }) + "\n");
}

export function notify(state: JourneyState, n: Omit<Notification, "id" | "at">) {
  state.notifications.push({ id: newId("ntf"), at: now(), ...n });
  if (state.notifications.length > 500) state.notifications.splice(0, state.notifications.length - 500);
}

/** Stage record for the current cycle. A new cycle starts every stage with no record. */
export function recordOf(state: JourneyState, stageId: number): StageRecord | undefined {
  return state.stages[`${state.cycle}:${stageId}`];
}
export function setRecord(state: JourneyState, stageId: number, rec: StageRecord) {
  state.stages[`${state.cycle}:${stageId}`] = rec;
}

/**
 * Stage 1 of every phase waits for the human's Ready to start on the dashboard. Starting a new phase is itself
 * the human's go decision, so it releases stage 1 of that phase. Every later stage needs no start signal: it
 * begins by itself when its predecessors are done.
 */
export function startBlocker(state: JourneyState, stage: StageDef): string | undefined {
  if (!stage.startSignal) return undefined;
  const released = state.cycle > 1 || state.startSignals.some((s) => s.cycle === state.cycle);
  return released
    ? undefined
    : `Stage ${stage.id} is waiting for the human to press Ready to start on the dashboard. Tell them and stop. Do not start it, and do not work on it in the meantime.`;
}

/** The next cycle may start only when both the Adaptation Plan (17) and Intent Refinement (18) are done. */
export function cycleStartBlockers(state: JourneyState, config: JourneyConfig, stages: StageDef[]): number[] {
  return [17, 18].filter((id) => {
    const s = stages.find((x) => x.id === id);
    return !s || effectiveStatus(state, config, s) !== "done";
  });
}

/** What an approval request is about: one document, or one epic's bundle. */
export function approvalKey(a: Approval): string {
  return a.epic !== undefined ? `epic:${a.epic}` : `${a.taskId}|${a.artifact}`;
}

/** The newest request per document or epic. An older revise or reject stops counting once a newer request exists. */
export function latestPerKey(approvals: Approval[]): Approval[] {
  const latest = new Map<string, Approval>();
  for (const a of approvals) {
    const prev = latest.get(approvalKey(a));
    if (!prev || a.requestedAt >= prev.requestedAt) latest.set(approvalKey(a), a);
  }
  return [...latest.values()];
}

/** Epics in this phase: every docs/user-stories/epic-N-*.md, narrowed by epicScope when the human set one. */
export function epicsInScope(config: JourneyConfig): string[] {
  const dir = join(repoRoot, "docs", "user-stories");
  const found = existsSync(dir) ? readdirSync(dir).map((f) => f.match(/^epic-(\d+)-/)?.[1]).filter((x): x is string => !!x) : [];
  const all = [...new Set(found)].sort((a, b) => Number(a) - Number(b));
  const scope = config.epicScope?.map(String);
  return scope ? all.filter((e) => scope.includes(e)) : all;
}

/** Where each in-scope epic stands for a per-epic stage (6 or 8) in the current cycle. */
export function epicCoverage(state: JourneyState, stage: StageDef, epics: string[]) {
  const latest = latestPerKey(state.approvals.filter((a) => a.stageId === stage.id && a.cycle === state.cycle && a.epic !== undefined));
  const of = (e: string) => latest.find((a) => a.epic === e);
  return {
    approved: epics.filter((e) => of(e)?.status === "approved"),
    pending: epics.filter((e) => of(e)?.status === "pending"),
    rework: epics.filter((e) => of(e)?.status === "revise" || of(e)?.status === "rejected"),
    missing: epics.filter((e) => !of(e)),
  };
}

/** Effective status: agent-reported status, adjusted by approvals in the current cycle. */
export function effectiveStatus(state: JourneyState, config: JourneyConfig, stage: StageDef): StageStatus {
  if (waiverFor(config, stage.id)) return "waived";
  const rec = recordOf(state, stage.id);
  const mine = state.approvals.filter((a) => a.stageId === stage.id && a.cycle === state.cycle);
  if (mine.some((a) => a.status === "pending")) return "awaiting_approval";
  if (rec?.status === "done" || rec?.status === "gap") return rec.status;
  if (latestPerKey(mine).some((a) => a.status === "revise" || a.status === "rejected")) return "changes_requested";
  return rec?.status ?? "not_started";
}

export function predecessorsCleared(state: JourneyState, config: JourneyConfig, stages: StageDef[], stage: StageDef) {
  const open: number[] = [];
  for (const id of stage.after) {
    const p = stages.find((s) => s.id === id);
    if (!p) continue;
    const st = effectiveStatus(state, config, p);
    if (st !== "done" && st !== "waived") open.push(id);
  }
  return open;
}

/** Latest approval per task for a stage in the current cycle. */
export function gateSummary(state: JourneyState, stage: StageDef) {
  return stage.gates.map((g) => {
    // an epic request counts toward every gate its items name
    const mine = state.approvals.filter(
      (a) => a.stageId === stage.id && a.cycle === state.cycle && (a.taskId === g.taskId || (a.items?.some((i) => i.taskId === g.taskId) ?? false)),
    );
    return {
      taskId: g.taskId,
      requested: mine.length,
      approved: mine.filter((a) => a.status === "approved").length,
      pending: mine.filter((a) => a.status === "pending").length,
      blocked: latestPerKey(mine).filter((a) => a.status === "rejected" || a.status === "revise").length,
    };
  });
}
