// Dashboard for the governance orchestrator. Zero dependencies, local only.
//
//   GOVERNANCE_APPROVAL_SECRET=<long random string> node dashboard/server.mjs
//
// It reads state.json (written by the agent's tools) and is the only writer of decisions.ndjson.
// Every decision line is HMAC-signed with GOVERNANCE_APPROVAL_SECRET; the agent's tools verify it.
// Start the agent server with the same secret. The agent has no shell, so it cannot read it.

import { createHmac, randomUUID, timingSafeEqual } from "node:crypto";
import { appendFileSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const projectRoot = resolve(here, "..");
const stateDir = process.env.GOVERNANCE_STATE_DIR ?? join(projectRoot, ".governance");
const port = Number(process.env.DASHBOARD_PORT ?? 4173);
const secret = process.env.GOVERNANCE_APPROVAL_SECRET;

if (!secret || secret.length < 16) {
  console.error("Set GOVERNANCE_APPROVAL_SECRET to a random string of at least 16 characters, and use the same value for the agent server.");
  process.exit(1);
}

const readJson = (p, fallback) => (existsSync(p) ? JSON.parse(readFileSync(p, "utf8")) : fallback);
const loadStages = () => JSON.parse(readFileSync(join(projectRoot, "journey", "stages.json"), "utf8"));
const loadConfig = () => JSON.parse(readFileSync(join(projectRoot, "journey", "journey.config.json"), "utf8"));
const sign = (d) =>
  createHmac("sha256", secret).update(JSON.stringify([d.approvalId, d.decision, d.note, d.decidedBy, d.decidedAt])).digest("hex");

const signCycle = (d) =>
  createHmac("sha256", secret).update(JSON.stringify(["cycle_start", d.note, d.decidedBy, d.decidedAt])).digest("hex");

const signStart = (d) =>
  createHmac("sha256", secret).update(JSON.stringify(["stage_start", d.stageId, d.cycle, d.note, d.decidedBy, d.decidedAt])).digest("hex");

const safeEqual = (a, b) => {
  if (typeof a !== "string" || typeof b !== "string") return false;
  const bufA = Buffer.from(a);
  const bufB = Buffer.from(b);
  if (bufA.length !== bufB.length) return false;
  return timingSafeEqual(bufA, bufB);
};

function verifiedDecisions() {
  const file = join(stateDir, "decisions.ndjson");
  if (!existsSync(file)) return { decisions: [], starts: [], signals: [] };
  const decisions = [];
  const starts = [];
  const signals = [];
  for (const raw of readFileSync(file, "utf8").split("\n")) {
    if (!raw.trim()) continue;
    try {
      const d = JSON.parse(raw);
      if (d.type === "cycle_start") {
        if (safeEqual(signCycle(d), d.sig)) starts.push({ note: d.note, decidedBy: d.decidedBy, decidedAt: d.decidedAt });
      } else if (d.type === "stage_start") {
        if (d.stageId === 1 && safeEqual(signStart(d), d.sig)) signals.push({ cycle: d.cycle, note: d.note, decidedBy: d.decidedBy, decidedAt: d.decidedAt });
      } else if (safeEqual(sign(d), d.sig)) decisions.push(d);
    } catch {
      /* ignore malformed line */
    }
  }
  starts.sort((a, b) => a.decidedAt.localeCompare(b.decidedAt));
  return { decisions, starts, signals };
}

function loadState() {
  const config = loadConfig();
  const state = readJson(join(stateDir, "state.json"), {
    version: 1, cycle: 1, updatedAt: null, stages: {}, approvals: [], notifications: [],
  });
  const { decisions, starts, signals } = verifiedDecisions();
  state.cycleStarts = starts;
  state.startSignals = signals;
  state.cycle = 1 + starts.length;
  for (const a of state.approvals) {
    if (a.reuse) { // an earlier accepted episode still stands: counts as approved without a new decision
      Object.assign(a, { status: "approved", decidedBy: "reused episode", decidedAt: a.reuse.recordedAt, note: a.reuse.summary });
      continue;
    }
    const d = decisions.find((x) => x.approvalId === a.id);
    a.status = d ? d.decision : "pending";
    if (d) Object.assign(a, { decidedBy: d.decidedBy, decidedAt: d.decidedAt, note: d.note });
  }
  return { state, config };
}

function waived(config, id) {
  const o = config.stageOverrides?.[String(id)];
  return o?.applicable === false && o.waiver?.reason && o.waiver?.approvedBy && o.waiver?.date ? o.waiver : null;
}

// Same rules as bot/lib/store.ts: the newest request per document or epic is the one that counts.
const approvalKey = (a) => (a.epic !== undefined ? `epic:${a.epic}` : `${a.taskId}|${a.artifact}`);
function latestPerKey(approvals) {
  const latest = new Map();
  for (const a of approvals) {
    const prev = latest.get(approvalKey(a));
    if (!prev || a.requestedAt >= prev.requestedAt) latest.set(approvalKey(a), a);
  }
  return [...latest.values()];
}

function epicsInScope(config) {
  const dir = join(projectRoot, "..", "docs", "user-stories");
  const found = existsSync(dir) ? readdirSync(dir).map((f) => f.match(/^epic-(\d+)-/)?.[1]).filter(Boolean) : [];
  const all = [...new Set(found)].sort((a, b) => Number(a) - Number(b));
  const scope = config.epicScope?.map(String);
  return scope ? all.filter((e) => scope.includes(e)) : all;
}

// How many decisions this stage asks of the human, and how many are done, waiting, or need rework.
function touchpointCounts(state, stage, epics) {
  const tp = stage.touchpoints;
  const latest = latestPerKey(state.approvals.filter((a) => a.stageId === stage.id && a.cycle === state.cycle));
  const count = (s) => latest.filter((a) => a.status === s).length;
  let approved = count("approved");
  let waiting = count("pending");
  let rework = count("revise") + count("rejected");
  let required = null;
  if (tp.kind === "per_epic") {
    const of = (e) => latest.find((a) => a.epic === e);
    required = epics.length;
    approved = epics.filter((e) => of(e)?.status === "approved").length;
    waiting = epics.filter((e) => of(e)?.status === "pending").length;
    rework = epics.filter((e) => ["revise", "rejected"].includes(of(e)?.status)).length;
  } else if (tp.kind === "fixed") {
    required = tp.count;
    approved = Math.min(approved, required); // stage 1 has two documents under one gate, so cap the count at what is asked
  }
  else if (tp.kind === "external" || tp.kind === "none") required = 0;
  const toCome = required === null ? null : Math.max(0, required - approved - waiting - rework);
  return { kind: tp.kind, label: tp.label, required, minimum: tp.minimum ?? null, approved, waiting, rework, toCome };
}

function effective(state, config, stage) {
  if (waived(config, stage.id)) return "waived";
  const rec = state.stages[`${state.cycle}:${stage.id}`];
  const mine = state.approvals.filter((a) => a.stageId === stage.id && a.cycle === state.cycle);
  if (mine.some((a) => a.status === "pending")) return "awaiting_approval";
  if (rec && (rec.status === "done" || rec.status === "gap")) return rec.status;
  if (latestPerKey(mine).some((a) => a.status === "revise" || a.status === "rejected")) return "changes_requested";
  return rec?.status ?? "not_started";
}

// ---- Launching the orchestrator on Claude Code ------------------------------------------------------------
// The dashboard starts `claude --agent governance-orchestrator` headless. Prompts are fixed here; nothing the page
// sends becomes part of a prompt. The secret reaches the MCP server through the environment, never through a file.
//   GOVERNANCE_RUN=off                 never launch (the buttons only record your decisions)
//   GOVERNANCE_RUN_ALLOW_WRITES=1      let stage subagents draft documents (write_document); off by default
//   GOVERNANCE_RUN_BUDGET_USD=2        stop a run that would spend more than this
//   GOVERNANCE_RUN_TIMEOUT_MIN=20      stop a run that takes longer than this
//   GOVERNANCE_MODEL=haiku             model for the orchestrator itself; unset uses the agent file's model (sonnet)
const repoRoot = resolve(projectRoot, "..");
const runsDir = join(stateDir, "runs");
const RUN_ENABLED = process.env.GOVERNANCE_RUN !== "off";
const ALLOW_WRITES = process.env.GOVERNANCE_RUN_ALLOW_WRITES === "1";
const BUDGET_USD = process.env.GOVERNANCE_RUN_BUDGET_USD ?? "2";
const TIMEOUT_MIN = Number(process.env.GOVERNANCE_RUN_TIMEOUT_MIN ?? 20);
const GOV_TOOLS = ["journey_status", "check_approvals", "check_reuse", "report_stage", "request_approval", "notify", "run_command", ...(ALLOW_WRITES ? ["write_document"] : [])];
let run = null;

function launchOrchestrator(reason, prompt) {
  if (!RUN_ENABLED) return { launched: false, why: "Launching is switched off (GOVERNANCE_RUN=off)." };
  if (run?.status === "running") return { launched: false, why: "The orchestrator is already running." };
  mkdirSync(runsDir, { recursive: true });
  const cfg = join(stateDir, "claude-mcp.json");
  writeFileSync(cfg, JSON.stringify({
    mcpServers: { governance: {
      command: "node",
      args: [join(projectRoot, "node_modules", "tsx", "dist", "cli.mjs"), join(projectRoot, "mcp", "server.ts")],
      env: { GOVERNANCE_APPROVAL_SECRET: secret, GOVERNANCE_STATE_DIR: stateDir },
    } },
  }, null, 2));
  const allowed = ["Agent", "Read", "Grep", "Glob", ...GOV_TOOLS.map((t) => `mcp__governance__${t}`)].join(",");
  const id = new Date().toISOString().replace(/[:.]/g, "-");
  run = { id, reason, status: "running", startedAt: new Date().toISOString(), endedAt: null, calls: [], result: "", costUsd: null, turns: null, error: null, writesAllowed: ALLOW_WRITES };
  const mine = run;
  const log = join(runsDir, `${id}.ndjson`);
  let child;
  try {
    child = spawn("claude", ["-p", prompt, "--agent", "governance-orchestrator", "--mcp-config", cfg, "--strict-mcp-config",
      ...(process.env.GOVERNANCE_MODEL ? ["--model", process.env.GOVERNANCE_MODEL] : []), "--allowedTools", allowed, "--max-budget-usd", String(BUDGET_USD), "--no-session-persistence", "--output-format", "stream-json", "--verbose"],
      { cwd: repoRoot, env: { ...process.env, GOVERNANCE_STATE_DIR: stateDir }, windowsHide: true, stdio: ["ignore", "pipe", "pipe"] });
  } catch (e) {
    mine.status = "failed"; mine.endedAt = new Date().toISOString(); mine.error = String(e.message ?? e);
    return { launched: false, why: mine.error };
  }
  let buf = "";
  let errText = "";
  const timer = setTimeout(() => { mine.error = `Stopped after ${TIMEOUT_MIN} minutes.`; child.kill(); }, TIMEOUT_MIN * 60_000);
  child.stdout.on("data", (chunk) => {
    appendFileSync(log, chunk);
    buf += chunk.toString("utf8");
    let nl;
    while ((nl = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, nl).trim();
      buf = buf.slice(nl + 1);
      if (!line) continue;
      try {
        const e = JSON.parse(line);
        if (e.type === "assistant") {
          for (const c of e.message?.content ?? []) {
            if (c.type === "tool_use") {
              const name = c.name.replace("mcp__governance__", "");
              mine.calls.push({ at: new Date().toISOString(), subagent: Boolean(e.parent_tool_use_id), name: c.name === "Agent" ? `Agent -> ${c.input?.subagent_type ?? ""}` : name });
              if (mine.calls.length > 200) mine.calls.shift();
            }
          }
        } else if (e.type === "result") {
          mine.result = String(e.result ?? "").slice(0, 6000);
          mine.costUsd = e.total_cost_usd ?? null;
          mine.turns = e.num_turns ?? null;
          if (e.is_error) mine.error = mine.result || "The run reported an error.";
        }
      } catch { /* ignore a partial or non-JSON line */ }
    }
  });
  child.stderr.on("data", (d) => { errText = (errText + d.toString("utf8")).slice(-1500); });
  child.on("error", (e) => {
    clearTimeout(timer);
    mine.status = "failed"; mine.endedAt = new Date().toISOString();
    mine.error = e.code === "ENOENT" ? "The claude command was not found. Install Claude Code and make sure `claude` is on PATH." : String(e.message ?? e);
  });
  child.on("close", (code) => {
    clearTimeout(timer);
    if (mine.status !== "running") return;
    mine.endedAt = new Date().toISOString();
    mine.status = mine.error || (code !== 0 && !mine.result) ? "failed" : "finished";
    if (mine.status === "failed" && !mine.error) mine.error = errText.trim() || `claude exited with code ${code}.`;
  });
  return { launched: true };
}

function snapshot() {
  const { stages, gateModes } = loadStages();
  const { state, config } = loadState();
  const blockers = [17, 18].filter((id) => {
    const s = stages.find((x) => x.id === id);
    return !s || effective(state, config, s) !== "done";
  });
  // Stage 1 of every phase waits for Ready to start. Starting a new phase is itself that go decision.
  const signal = state.startSignals.find((x) => x.cycle === state.cycle);
  const readyToStart = state.cycle > 1
    ? { awaiting: false, by: state.cycleStarts[state.cycle - 2].decidedBy, at: state.cycleStarts[state.cycle - 2].decidedAt, viaPhaseStart: true }
    : signal ? { awaiting: false, by: signal.decidedBy, at: signal.decidedAt, viaPhaseStart: false } : { awaiting: true };
  const epics = epicsInScope(config);
  const rows = stages.map((s) => ({ id: s.id, ...touchpointCounts(state, s, epics) }));
  const sum = (key) => rows.reduce((n, r) => n + (r[key] ?? 0), 0);
  return {
    now: new Date().toISOString(),
    cycle: state.cycle,
    readyToStart,
    orchestrator: {
      enabled: RUN_ENABLED,
      writesAllowed: ALLOW_WRITES,
      budgetUsd: BUDGET_USD,
      run: run && { ...run, calls: run.calls.slice(-30) },
    },
    epicCount: epics.length,
    approvalsAhead: {
      rows,
      knownTotal: sum("required"),
      approved: sum("approved"),
      waiting: sum("waiting"),
      rework: sum("rework"),
      toCome: sum("toCome"),
      variableStages: rows.filter((r) => r.kind === "variable").map((r) => r.id),
    },
    phaseStarts: state.cycleStarts.map((c, i) => ({ cycle: i + 2, ...c })),
    cycleBlockers: blockers,
    profile: config.profile,
    approver: process.env.GOVERNANCE_APPROVER ?? config.approver,
    updatedAt: state.updatedAt,
    gateModes,
    stages: stages.map((s) => ({
      ...s,
      effective: effective(state, config, s),
      waiver: waived(config, s.id),
      record: state.stages[`${state.cycle}:${s.id}`] ?? null,
      approvals: state.approvals.filter((a) => a.stageId === s.id && a.cycle === state.cycle),
    })),
    notifications: state.notifications.slice(-100).reverse(),
  };
}

function send(res, code, body, type = "application/json; charset=utf-8") {
  res.writeHead(code, { "content-type": type, "cache-control": "no-store", "x-content-type-options": "nosniff" });
  res.end(typeof body === "string" ? body : JSON.stringify(body));
}

const readBody = (req) =>
  new Promise((ok, fail) => {
    let size = 0;
    const chunks = [];
    req.on("data", (c) => {
      size += c.length;
      if (size > 20_000) { fail(new Error("body too large")); req.destroy(); return; }
      chunks.push(c);
    });
    req.on("end", () => ok(Buffer.concat(chunks).toString("utf8")));
    req.on("error", fail);
  });

const allowedOrigins = new Set([`http://127.0.0.1:${port}`, `http://localhost:${port}`]);

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url ?? "/", `http://127.0.0.1:${port}`);
    if (req.method === "GET" && url.pathname === "/") {
      return send(res, 200, readFileSync(join(here, "index.html"), "utf8"), "text/html; charset=utf-8");
    }
    if (req.method === "GET" && url.pathname === "/api/state") return send(res, 200, snapshot());
    if (req.method === "POST" && url.pathname === "/api/decision") {
      if (req.headers["x-requested-with"] !== "governance-dashboard" || !allowedOrigins.has(String(req.headers.origin))) {
        return send(res, 403, { error: "forbidden" });
      }
      const body = JSON.parse(await readBody(req));
      const { approvalId, decision } = body;
      const note = String(body.note ?? "").trim();
      if (!["approved", "revise", "rejected"].includes(decision)) return send(res, 400, { error: "decision must be approved, revise or rejected" });
      if (decision !== "approved" && note.length < 3) return send(res, 400, { error: "a note is required when you do not approve" });
      const { state } = loadState();
      const a = state.approvals.find((x) => x.id === approvalId);
      if (!a) return send(res, 404, { error: "unknown approval" });
      if (a.status !== "pending") return send(res, 409, { error: `already decided: ${a.status}` });
      const line = { approvalId, decision, note, decidedBy: process.env.GOVERNANCE_APPROVER ?? loadConfig().approver, decidedAt: new Date().toISOString() };
      line.sig = sign(line);
      mkdirSync(stateDir, { recursive: true });
      appendFileSync(join(stateDir, "decisions.ndjson"), JSON.stringify(line) + "\n");
      appendFileSync(join(stateDir, "events.ndjson"), JSON.stringify({ at: line.decidedAt, type: "decision", approvalId, decision, id: randomUUID().slice(0, 8) }) + "\n");
      return send(res, 200, { ok: true });
    }
    if (req.method === "POST" && url.pathname === "/api/start") {
      if (req.headers["x-requested-with"] !== "governance-dashboard" || !allowedOrigins.has(String(req.headers.origin))) {
        return send(res, 403, { error: "forbidden" });
      }
      const body = JSON.parse(await readBody(req));
      const snap = snapshot();
      if (!snap.readyToStart.awaiting) return send(res, 409, { error: "stage 1 was already released for this phase" });
      if (Number(body.expectCycle) !== snap.cycle) return send(res, 409, { error: "the phase changed, reload the page" });
      const line = { type: "stage_start", stageId: 1, cycle: snap.cycle, note: "", decidedBy: process.env.GOVERNANCE_APPROVER ?? loadConfig().approver, decidedAt: new Date().toISOString() };
      line.sig = signStart(line);
      mkdirSync(stateDir, { recursive: true });
      appendFileSync(join(stateDir, "decisions.ndjson"), JSON.stringify(line) + "\n");
      appendFileSync(join(stateDir, "events.ndjson"), JSON.stringify({ at: line.decidedAt, type: "stage_released", stageId: 1, cycle: snap.cycle }) + "\n");
      const launch = body.launch === false
        ? { launched: false, why: "You chose not to start the orchestrator." }
        : launchOrchestrator("Ready to start", `The human pressed Ready to start for stage 1 of Phase ${snap.cycle}. Take stage 1 through to an approval request, then continue stage by stage as your instructions say. Stop at the first pending approval, blocked stage or gap.`);
      return send(res, 200, { ok: true, launch });
    }
    if (req.method === "POST" && url.pathname === "/api/run") {
      if (req.headers["x-requested-with"] !== "governance-dashboard" || !allowedOrigins.has(String(req.headers.origin))) {
        return send(res, 403, { error: "forbidden" });
      }
      if (snapshot().readyToStart.awaiting) return send(res, 409, { error: "Press Ready to start first." });
      const launch = launchOrchestrator("Continue", "The human asked you to continue. Check the journey and the approvals, act on any decisions, and carry on as your instructions say. Stop at the first pending approval, blocked stage or gap.");
      return launch.launched ? send(res, 200, { ok: true, launch }) : send(res, 409, { error: launch.why });
    }
    if (req.method === "POST" && url.pathname === "/api/cycle") {
      if (req.headers["x-requested-with"] !== "governance-dashboard" || !allowedOrigins.has(String(req.headers.origin))) {
        return send(res, 403, { error: "forbidden" });
      }
      const body = JSON.parse(await readBody(req));
      const note = String(body.note ?? "").trim();
      if (note.length < 10) return send(res, 400, { error: "write your go decision for the next phase (at least 10 characters)" });
      const snap = snapshot();
      if (snap.cycleBlockers.length) return send(res, 409, { error: `stage(s) ${snap.cycleBlockers.join(" and ")} must be done first` });
      if (Number(body.expectCycle) !== snap.cycle) return send(res, 409, { error: "the cycle changed, reload the page" });
      const line = { type: "cycle_start", note, decidedBy: process.env.GOVERNANCE_APPROVER ?? loadConfig().approver, decidedAt: new Date().toISOString() };
      line.sig = signCycle(line);
      mkdirSync(stateDir, { recursive: true });
      appendFileSync(join(stateDir, "decisions.ndjson"), JSON.stringify(line) + "\n");
      appendFileSync(join(stateDir, "events.ndjson"), JSON.stringify({ at: line.decidedAt, type: "cycle_started", cycle: snap.cycle + 1 }) + "\n");
      return send(res, 200, { ok: true, cycle: snap.cycle + 1 });
    }
    send(res, 404, { error: "not found" });
  } catch (err) {
    send(res, 500, { error: String(err?.message ?? err) });
  }
});

server.listen(port, "127.0.0.1", () => {
  console.log(`Governance dashboard: http://127.0.0.1:${port}  (state: ${stateDir})`);
});
