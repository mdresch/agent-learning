import { appendFileSync, existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, relative, resolve, sep } from "node:path";
import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { loadStages, loadState, logEvent, repoRoot } from "../lib/store.js";

// Documents produced by tooling or frozen by policy. The agent never writes these.
const GENERATED = [
  "docs/project-docs/Project-Management-Plan.md",
  "docs/project-docs/management-plans/",
  "docs/project-docs/Status-Reports/",
  "governance-orchestrator/",
];

export default defineTool({
  description:
    "Write a governance document for a stage. The path must be inside that stage's writes list in journey/stages.json. Generated plans (PMP, management plans, status reports) are refused: regenerate them with the pmbok-planning tooling. An artifact with an approved approval is a frozen baseline: replace is refused and the change goes through Stage 16. Registers are append-only.",
  effect: "write",
  dryRunResult: ({ path, mode }) => ({ written: false, path, mode }),
  inputSchema: z.object({
    stageId: z.number().int(),
    path: z.string().describe("Repo-relative path, forward slashes."),
    mode: z.enum(["create", "append", "replace"]),
    content: z.string().min(1),
  }),
  async execute({ stageId, path, mode, content }, ctx) {
    const { stages } = loadStages();
    const stage = stages.find((s) => s.id === stageId);
    if (!stage) throw new Error(`Unknown stage ${stageId}`);

    const abs = resolve(repoRoot, path);
    const rel = relative(repoRoot, abs).split(sep).join("/");
    if (rel.startsWith("..") || rel === "") throw new Error("Path is outside the repository.");
    if (GENERATED.some((g) => rel === g || rel.startsWith(g))) throw new Error(`${rel} is generated or protected. Use the tooling or ask the human.`);
    if (!stage.writes.some((w) => rel === w || (w.endsWith("/") && rel.startsWith(w)))) {
      throw new Error(`Stage ${stageId} may not write ${rel}. Allowed: ${stage.writes.join(", ") || "nothing"}.`);
    }

    if (mode === "replace") {
      const { state } = loadState();
      const frozen = state.approvals.find((a) => a.status === "approved" && (a.artifact === rel || (a.items?.some((i) => i.artifact === rel) ?? false)));
      if (frozen) {
        throw new Error(`${rel} was approved (${frozen.id}) and is a frozen baseline. Do not replace it: classify the diff in Stage 16 (classify-diff-type).`);
      }
    }
    if (mode === "create" && existsSync(abs)) throw new Error(`${rel} already exists. Use append, or replace if it is not frozen.`);
    if (mode !== "create" && !existsSync(abs) && mode === "append") throw new Error(`${rel} does not exist; nothing to append to.`);

    mkdirSync(dirname(abs), { recursive: true });
    if (mode === "append") appendFileSync(abs, content.startsWith("\n") ? content : `\n${content}`);
    else writeFileSync(abs, content);
    logEvent("document_written", { stageId, path: rel, mode, session: ctx.session.id });
    return { written: true, path: rel, mode, bytes: Buffer.byteLength(content) };
  },
});
