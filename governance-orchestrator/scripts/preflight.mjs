// Is everything in place for the full run to start from the dashboard's Ready to start button?
//
//   npm run preflight
//
// No model is called. It reads the repo, runs read-only git and agent-learn commands, and starts the MCP server once.
// Exit code 1 if anything blocks a run; warnings do not.

import { execFile } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync, rmSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const projectRoot = resolve(here, "..");
const repoRoot = resolve(projectRoot, "..");
const run = (cmd, args, opts = {}) => new Promise((ok) => execFile(cmd, args, { cwd: repoRoot, timeout: 90_000, maxBuffer: 20_000_000, windowsHide: true, ...opts }, (e, stdout, stderr) => ok({ code: e ? (typeof e.code === "number" ? e.code : 1) : 0, stdout, stderr })));
const { stages, defaultAgentId } = JSON.parse(readFileSync(join(projectRoot, "journey", "stages.json"), "utf8"));
const config = JSON.parse(readFileSync(join(projectRoot, "journey", "journey.config.json"), "utf8"));

const rows = [];
const add = (level, name, detail, fix = "") => rows.push({ level, name, detail, fix });
const ok = (n, d) => add("ok", n, d);
const warn = (n, d, f) => add("warn", n, d, f);
const fail = (n, d, f) => add("FAIL", n, d, f);

// 1. Tools on this machine
const cl = await run("claude", ["--version"]);
cl.code === 0 ? ok("Claude Code CLI", cl.stdout.trim()) : fail("Claude Code CLI", "`claude` was not found on PATH", "Install Claude Code, then run `claude` once to log in");
const uv = await run("uv", ["--version"]);
uv.code === 0 ? ok("uv", uv.stdout.trim()) : fail("uv", "`uv` not found", "Install uv; the policy checks run through `uv run agent-learn`");

// 2. Secret and state
const secret = process.env.GOVERNANCE_APPROVAL_SECRET ?? "";
secret.length >= 16
  ? ok("Approval secret", "GOVERNANCE_APPROVAL_SECRET is set in this shell")
  : fail("Approval secret", secret ? "set but shorter than 16 characters" : "GOVERNANCE_APPROVAL_SECRET is not set in this shell", "export GOVERNANCE_APPROVAL_SECRET=<random string> in the shell that starts the dashboard AND claude");
const stateDir = process.env.GOVERNANCE_STATE_DIR ?? join(projectRoot, ".governance");
try { mkdirSync(stateDir, { recursive: true }); const t = join(stateDir, ".write-test"); writeFileSync(t, "x"); rmSync(t); ok("State folder", `${stateDir} is writable`); } catch (e) { fail("State folder", `${stateDir} is not writable: ${e.message}`, "Fix permissions or set GOVERNANCE_STATE_DIR"); }
if (existsSync(join(stateDir, "state.json"))) {
  const st = JSON.parse(readFileSync(join(stateDir, "state.json"), "utf8"));
  warn("Existing journey", `${Object.keys(st.stages).length} stage record(s) and ${st.approvals.length} approval(s) already in ${stateDir}`, "Intended if you are resuming. For a clean start, use a new GOVERNANCE_STATE_DIR");
} else ok("Existing journey", "none: the first press of Ready to start begins Phase 1");

// 3. Agent files and tool server
const gen = await run("node", [join(here, "build-claude-agents.mjs"), "--check"]);
gen.code === 0 ? ok("Claude agent files", "up to date with bot/") : fail("Claude agent files", "out of date", "Run `npm run build:claude`");
try {
  const require = createRequire(join(projectRoot, "package.json"));
  const { Client } = await import(pathToFileURL(require.resolve("@modelcontextprotocol/sdk/client/index.js")).href);
  const { StdioClientTransport } = await import(pathToFileURL(require.resolve("@modelcontextprotocol/sdk/client/stdio.js")).href);
  const scratch = join(process.env.TEMP ?? projectRoot, "gov-preflight");
  mkdirSync(scratch, { recursive: true });
  const transport = new StdioClientTransport({ command: "node", args: [join(projectRoot, "node_modules", "tsx", "dist", "cli.mjs"), join(projectRoot, "mcp", "server.ts")], cwd: repoRoot, env: { ...process.env, GOVERNANCE_APPROVAL_SECRET: secret || "preflight-secret-0123456789", GOVERNANCE_STATE_DIR: scratch } });
  const client = new Client({ name: "preflight", version: "1" });
  await client.connect(transport);
  const names = (await client.listTools()).tools.map((t) => t.name);
  await client.close();
  rmSync(scratch, { recursive: true, force: true });
  names.length >= 8 ? ok("Tool server", `starts and lists ${names.length} tools`) : fail("Tool server", `only ${names.length} tools: ${names.join(", ")}`, "Check mcp/server.ts");
} catch (e) { fail("Tool server", `did not start: ${String(e.message ?? e).slice(0, 160)}`, "Run `npm install` in governance-orchestrator, then try again"); }
const mcp = JSON.parse(readFileSync(join(repoRoot, ".mcp.json"), "utf8"));
mcp.mcpServers?.governance ? ok("MCP registration", ".mcp.json names the governance server (Claude Code asks you to approve it once)") : fail("MCP registration", ".mcp.json has no governance server", "Restore .mcp.json");

// 4. Gate policies and what each already has on record
const gates = [...new Set(stages.flatMap((s) => s.gates.map((g) => g.taskId)))];
const missingPolicies = [];
const episodeCounts = {};
for (let i = 0; i < gates.length; i += 4) {
  await Promise.all(gates.slice(i, i + 4).map(async (g) => {
    const p = await run("uv", ["run", "agent-learn", "task-policy", "--agent-id", defaultAgentId, "--task-id", g]);
    if (p.code !== 0 || !p.stdout.includes("current_policy")) missingPolicies.push(g);
    const c = await run("uv", ["run", "agent-learn", "task-episodes-count", defaultAgentId, "--task-id", g]);
    episodeCounts[g] = c.code === 0 ? Number(c.stdout.trim().split(/\s+/).pop()) : null;
  }));
}
missingPolicies.length
  ? fail("Gate policies", `${gates.length - missingPolicies.length} of ${gates.length} registered. Missing: ${missingPolicies.join(", ")}`, "Create each with `agent-learn task-policy-init` (see the policy shapes in docs/policy-shapes) before its stage can be decided")
  : ok("Gate policies", `all ${gates.length} gate policies are registered`);
const withEp = gates.filter((g) => episodeCounts[g] > 0);
const noEp = gates.filter((g) => !(episodeCounts[g] > 0));
ok("Existing episodes", `${withEp.length} gate(s) already have episodes (reusable if unchanged): ${withEp.map((g) => `${g} x${episodeCounts[g]}`).join(", ") || "none"}`);
if (noEp.length) warn("Gates with no episode", noEp.join(", "), "Each needs its first human approval and episode. The orchestrator will record a gap, never backfill one");

// 5. Repository state
const gitSt = await run("git", ["status", "--porcelain"]);
const lines = gitSt.stdout.split("\n").filter(Boolean);
const conflicts = lines.filter((l) => /^(UU|AA|DU|UD|AU|UA|DD) /.test(l));
conflicts.length ? fail("Merge conflicts", `${conflicts.length} unresolved: ${conflicts.map((l) => l.slice(3)).join(", ")}`, "Resolve or abort the merge. Stage 8 requires a clean base, and a worktree forks from committed state only") : ok("Merge conflicts", "none");
const dirty = lines.filter((l) => !/^(UU|AA|DU|UD|AU|UA|DD) /.test(l));
dirty.length ? warn("Uncommitted changes", `${dirty.length} path(s), for example ${dirty.slice(0, 3).map((l) => l.slice(3)).join(", ")}`, "Stage 8 reads `git status` and will flag these. Commit or stash anything a story depends on") : ok("Uncommitted changes", "none");
const wt = await run("git", ["worktree", "list"]);
const extra = wt.stdout.split("\n").filter(Boolean).slice(1);
extra.length ? warn("Leftover worktrees", `${extra.length}: ${extra.map((l) => l.split(/\s+/)[0].split("/").pop()).join(", ")}`, "A branch or worktree for a story means a run already started. Stage 8 and 9 will report it and not adopt it") : ok("Leftover worktrees", "none");
const br = await run("git", ["branch", "--show-current"]);
ok("Branch", br.stdout.trim() || "(detached)");

// 6. Documents each stage needs, and the epics stages 6 and 8 will walk
const missing = [];
for (const s of stages) for (const a of s.artifacts) if (a && !existsSync(join(repoRoot, a))) missing.push(`stage ${s.id}: ${a}`);
missing.length ? warn("Stage documents", `not present yet: ${missing.join("; ")}`, "Expected for stages whose documents are created during the run (for example the Intent Refinement Proposal)") : ok("Stage documents", "every listed document exists");
const storiesDir = join(repoRoot, "docs", "user-stories");
const epicFiles = existsSync(storiesDir) ? readdirSync(storiesDir).filter((f) => /^epic-\d+-/.test(f)) : [];
const scope = config.epicScope?.map(String);
const inScope = epicFiles.filter((f) => !scope || scope.includes(f.match(/^epic-(\d+)-/)[1]));
const broken = [];
for (const f of inScope) {
  const head = readFileSync(join(storiesDir, f), "utf8").split("\n").slice(0, 12).join("\n");
  const links = [...head.matchAll(/\]\(([^)]+\.md)\)/g)].map((m) => m[1]);
  if (links.length < 3) { broken.push(`${f} (names ${links.length} of ADR, BRD, FDD)`); continue; }
  for (const l of links) if (!existsSync(resolve(storiesDir, l))) broken.push(`${f} -> ${l}`);
}
broken.length
  ? warn("Epic documents", `${inScope.length} epic(s) in scope, ${broken.length} broken or missing link(s): ${broken.slice(0, 4).join("; ")}${broken.length > 4 ? "..." : ""}`, "Stages 6 and 8 review an epic's ADR, BRD, FDD and stories as one request, so each epic needs all of them")
  : ok("Epic documents", `${inScope.length} epic(s) in scope; each names an ADR, BRD and FDD that exist`);
// Epics already implemented: stage 8 is the pre-implementation gate, so it does not apply to them
const status = (f) => [...readFileSync(join(storiesDir, f), "utf8").matchAll(/^\*\*Status:\*\*\s*([A-Za-z]+)/gm)].map((m) => m[1]);
const finished = inScope.filter((f) => { const st = status(f); return st.length > 0 && st.every((x) => x === "Completed"); }).map((f) => f.match(/^epic-(\d+)-/)[1]);
finished.length
  ? warn("Epics already built", `${finished.length} of ${inScope.length} in-scope epic(s) have every story Completed: ${finished.join(", ")}. Stage 8 (readiness before implementation) does not apply to them`, "Set epicScope in journey/journey.config.json to the epics this phase will implement, so stage 8 and its approvals only cover real work")
  : ok("Epics already built", "none of the in-scope epics are fully implemented");
scope ? ok("Phase scope", `epicScope limits stages 6 and 8 to ${scope.join(", ")}`) : warn("Phase scope", `no epicScope: stages 6 and 8 cover all ${epicFiles.length} epics (${epicFiles.length * 2} epic requests)`, "Set epicScope in journey/journey.config.json to the epics this phase should cover");
const waivers = Object.keys(config.stageOverrides ?? {});
waivers.length ? warn("Waivers", `stage(s) ${waivers.join(", ")} are waived`, "Intended? A waiver removes the stage from the path") : ok("Waivers", "none");

// 7. Run settings
ok("Run limits", `budget $${process.env.GOVERNANCE_RUN_BUDGET_USD ?? 2} per run, ${process.env.GOVERNANCE_RUN_TIMEOUT_MIN ?? 20} min, writes ${process.env.GOVERNANCE_RUN_ALLOW_WRITES === "1" ? "ALLOWED" : "off (review only)"}, launching ${process.env.GOVERNANCE_RUN === "off" ? "OFF" : "available"}`);
const up = await fetch("http://127.0.0.1:4173/api/state").then((r) => r.ok).catch(() => false);
up ? ok("Dashboard", "answering on http://127.0.0.1:4173") : warn("Dashboard", "not running on port 4173", "Start it with `npm run dashboard` in a shell that has GOVERNANCE_APPROVAL_SECRET set");

// Report
const icon = { ok: "ok  ", warn: "WARN", FAIL: "FAIL" };
console.log("");
for (const r of rows) console.log(`${icon[r.level]}  ${r.name.padEnd(22)} ${r.detail}${r.fix ? `\n      -> ${r.fix}` : ""}`);
const f = rows.filter((r) => r.level === "FAIL").length, w = rows.filter((r) => r.level === "warn").length;
console.log(`\n${f} blocking, ${w} warning(s), ${rows.length - f - w} ok. ${f ? "Fix the blocking items before pressing Ready to start." : "Nothing blocks a run."}`);
process.exit(f ? 1 : 0);
