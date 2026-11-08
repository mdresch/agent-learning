import { execFile } from "node:child_process";
import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { repoRoot } from "../lib/store.js";

// No shell is involved: argv goes straight to execFile. Only these forms run.
// Deliberately absent: task-policy-adjudicate and task-episode-register (a human records the gate),
// git commit/push/merge, gh pr merge/review/comment, and anything that edits code.
const AGENT_LEARN_READ = new Set(["list", "tasks-list", "task-policy", "task-policy-decide", "task-episodes-count", "task-episodes-list"]);
const GIT_READ = new Set(["status", "log", "diff", "show", "branch", "ls-files", "check-ignore", "rev-parse", "worktree"]);
const GH_PR_READ = new Set(["view", "list", "checks", "diff"]);
const DENY_ARG = /^(--output|--exec|--upload-pack|--ext-diff)($|=)|^-(c|o)($|=)/;

function allowed(argv: string[]): string | undefined {
  const [bin, a, b] = argv;
  if (argv.some((x) => DENY_ARG.test(x))) return "argument not allowed";
  if (bin === "uv" && a === "run" && (b === "agent-learn" || b === "agent-learn-ext")) {
    return AGENT_LEARN_READ.has(argv[3] ?? "") ? undefined : `${b} ${argv[3]} is not allowed`;
  }
  if (bin === "uv" && a === "run" && b === "pytest") {
    const pytestArgs = argv.slice(3);
    for (const arg of pytestArgs) {
      if (arg.startsWith("-o") || arg.startsWith("-c") || arg.startsWith("--override-ini") || arg.startsWith("--import-mode")) {
        return `pytest argument ${arg} is not allowed`;
      }
      if (!arg.startsWith("-") && !arg.startsWith("tests/") && !arg.startsWith("tests\\")) {
        return `pytest path ${arg} must be within tests/`;
      }
    }
    return undefined;
  }
  if (bin === "uv" && a === "run" && b === "python") return argv[3] === "scripts/phase_rollup.py" ? undefined : "only scripts/phase_rollup.py may run";
  if (bin === "git") {
    if (!GIT_READ.has(a ?? "")) return `git ${a} is not allowed`;
    if (a === "worktree" && b !== "list") return "only git worktree list is allowed";
    if (a === "branch" && argv.slice(2).some((x) => !x.startsWith("-") || /^-(d|D|m|M|c|C)/.test(x))) return "git branch may only list";
    return undefined;
  }
  if (bin === "gh" && a === "pr") return GH_PR_READ.has(b ?? "") ? undefined : `gh pr ${b} is not allowed`;
  return "command is not on the allowlist";
}

export default defineTool({
  description:
    "Run one allowlisted command from the repository root and return its output. Allowed: uv run agent-learn (list, tasks-list, task-policy, task-policy-decide, task-episodes-count, task-episodes-list), uv run pytest, uv run python scripts/phase_rollup.py, read-only git, read-only gh pr (view, list, checks, diff). Gate adjudication, episode registration, commits, pushes and merges are human actions and are refused.",
  effect: "write",
  dryRunResult: ({ argv }) => ({ ran: false, argv }),
  inputSchema: z.object({
    argv: z.array(z.string()).min(1).describe('Program and arguments, for example ["git","status","--short"].'),
    timeoutSeconds: z.number().int().min(1).max(600).optional().describe("Default 120, or 300 for pytest: the full suite takes about two minutes and more when the machine is busy."),
  }),
  async execute({ argv, timeoutSeconds }) {
    const reason = allowed(argv);
    if (reason) throw new Error(`Refused: ${reason}.`);
    const [bin, ...args] = argv;
    return await new Promise((resolve) => {
      const limit = timeoutSeconds ?? (argv.includes("pytest") ? 300 : 120);
      execFile(bin!, args, { cwd: repoRoot, timeout: limit * 1000, maxBuffer: 4_000_000, windowsHide: true }, (err, stdout, stderr) => {
        const cut = (s: string) => (s.length > 20_000 ? `${s.slice(0, 20_000)}\n[truncated ${s.length - 20_000} chars]` : s);
        resolve({
          exitCode: err ? ((err as NodeJS.ErrnoException & { code?: number | string }).code ?? 1) : 0,
          stdout: cut(stdout),
          stderr: cut(stderr),
        });
      });
    });
  },
});
