// Deciding, in code and without a model call, whether an earlier accepted gate episode still stands.
//
// An episode is reused only when ALL of these hold:
//   1. it was accepted (decision_disposition "accepted", action starts with "approve") and names this document
//   2. the document is unchanged since the commit the episode scored (artifact_commit), ignoring only the
//      Status row that recording the approval itself edits
//   3. the gate's TaskPolicy is the same one (id and version) the episode was decided under
//   4. the review criteria (stage requirements, gates and the subagent's instructions) are unchanged since the
//      episode was last reused (trust on first use: the episode itself does not store them)
// Anything else means the review runs again and a human approves it, so a new episode gets recorded.

import { createHash } from "node:crypto";
import { execFile } from "node:child_process";
import { readFileSync } from "node:fs";
import { basename, join } from "node:path";
import { projectRoot, repoRoot, type StageDef } from "./store.js";

export type EpisodeFacts = {
  id: string;
  createdAt: string;
  actionId: string;
  disposition: string | null;
  policyId: string | null;
  policyVersion: number | null;
  artifactCommit: string | null;
  robustUtility: number | null;
  expectedUtility: number | null;
  resultSummary: string;
  covers: string; // text that names the documents this episode judged
};

/** Lines whose change never counts as a content change. Recording an approval edits the Status row. */
export const DEFAULT_IGNORE = [String.raw`^\|\s*Status\s*\|`, String.raw`^\*\*Status:?\*\*`, String.raw`^Status:`, String.raw`^status:`];

export function parseJsonArray(stdout: string): unknown[] {
  const start = stdout.search(/^\[/m);
  if (start < 0) return [];
  const parsed = JSON.parse(stdout.slice(start));
  return Array.isArray(parsed) ? parsed : [];
}

export function toEpisodeFacts(raw: unknown): EpisodeFacts | undefined {
  const ep = (raw as { episode?: Record<string, unknown> })?.episode;
  if (!ep || typeof ep.id !== "string") return undefined;
  const md = (ep.metadata ?? {}) as Record<string, unknown>;
  const num = (v: unknown) => (typeof v === "number" ? v : null);
  return {
    id: ep.id,
    createdAt: String(ep.created_at ?? ""),
    actionId: String(ep.action_id ?? ""),
    disposition: typeof md.decision_disposition === "string" ? md.decision_disposition : null,
    policyId: typeof ep.policy_id === "string" ? ep.policy_id : null,
    policyVersion: num(ep.policy_version),
    artifactCommit: typeof md.artifact_commit === "string" ? md.artifact_commit : null,
    robustUtility: num(md.robust_utility),
    expectedUtility: num(md.expected_utility),
    resultSummary: String(ep.result_summary ?? ""),
    covers: `${ep.target ?? ""} ${ep.user_input ?? ""} ${ep.input_summary ?? ""}`,
  };
}

/** The newest accepted approval that names this document, or undefined. */
export function pickEpisode(episodes: EpisodeFacts[], artifact: string): EpisodeFacts | undefined {
  const name = basename(artifact);
  return episodes
    .filter((e) => e.disposition === "accepted" && /^approve/.test(e.actionId) && e.covers.includes(name))
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))[0];
}

/** Changed lines of a unified diff, minus those that match an ignore pattern. */
export function classifyDiff(diff: string, ignore: RegExp[]) {
  const changed: string[] = [];
  let ignored = 0;
  for (const line of diff.split("\n")) {
    if ((!line.startsWith("+") && !line.startsWith("-")) || line.startsWith("+++") || line.startsWith("---")) continue;
    const text = line.slice(1).trim();
    if (text === "") continue;
    if (ignore.some((re) => re.test(text))) ignored++;
    else changed.push(line.slice(0, 160));
  }
  return { changed, ignored };
}

export function policyMatches(ep: EpisodeFacts, current: { id: string; version: number }) {
  return ep.policyId === current.id && ep.policyVersion === current.version;
}

/** Hash of everything that shapes how this stage is reviewed. Any edit to it counts as changed reasoning. */
export function reviewBasisHash(stage: StageDef): string {
  const instructions = readFileSync(join(projectRoot, "bot", "subagents", stage.subagent, "instructions.md"), "utf8");
  const basis = JSON.stringify({ id: stage.id, requirements: stage.requirements, gates: stage.gates, touchpoints: stage.touchpoints, instructions });
  return createHash("sha256").update(basis).digest("hex");
}

export function run(cmd: string, args: string[]): Promise<{ code: number; stdout: string; stderr: string }> {
  return new Promise((resolve) => {
    execFile(cmd, args, { cwd: repoRoot, timeout: 120_000, maxBuffer: 20_000_000, windowsHide: true }, (err, stdout, stderr) => {
      const code = err ? Number((err as NodeJS.ErrnoException & { code?: number | string }).code ?? 1) : 0;
      resolve({ code: Number.isNaN(code) ? 1 : code, stdout, stderr });
    });
  });
}
