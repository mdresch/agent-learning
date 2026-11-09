// Stdio MCP server that exposes the governance tools to Claude Code.
// It wraps the same tool files the Grok agent uses (bot/tools/*.ts), so there is one implementation of every
// rule: stage ordering, approval gates, the command allowlist and the frozen-baseline check.
//
// Launched by the repo's .mcp.json. The approval secret comes from GOVERNANCE_APPROVAL_SECRET in that file's env
// block. The agent has no shell, so it cannot read it.

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import * as z from "zod";
import checkApprovals from "../bot/tools/check_approvals.js";
import checkReuse from "../bot/tools/check_reuse.js";
import journeyStatus from "../bot/tools/journey_status.js";
import notify from "../bot/tools/notify.js";
import reportStage from "../bot/tools/report_stage.js";
import requestApproval from "../bot/tools/request_approval.js";
import runCommand from "../bot/tools/run_command.js";
import writeDocument from "../bot/tools/write_document.js";
import { repoRoot, stateDir } from "../bot/lib/store.js";

type Tool = {
  description: string;
  effect?: string;
  inputSchema: z.ZodType;
  execute: (input: unknown, ctx: unknown) => Promise<unknown> | unknown;
};

const tools: Record<string, Tool> = {
  journey_status: journeyStatus as unknown as Tool,
  check_approvals: checkApprovals as unknown as Tool,
  check_reuse: checkReuse as unknown as Tool,
  report_stage: reportStage as unknown as Tool,
  request_approval: requestApproval as unknown as Tool,
  notify: notify as unknown as Tool,
  run_command: runCommand as unknown as Tool,
  write_document: writeDocument as unknown as Tool,
};

const server = new Server({ name: "governance", version: "0.1.0" }, { capabilities: { tools: {} } });

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: Object.entries(tools).map(([name, t]) => ({
    name,
    description: t.description,
    inputSchema: z.toJSONSchema(t.inputSchema, { io: "input" }) as { type: "object" },
    annotations: { readOnlyHint: t.effect === "read" },
  })),
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const tool = tools[req.params.name];
  if (!tool) return { isError: true, content: [{ type: "text", text: `Unknown tool ${req.params.name}` }] };
  try {
    const input = tool.inputSchema.parse(req.params.arguments ?? {});
    const ctx = {
      toolCallId: `mcp-${Date.now()}`,
      session: { id: "claude-code", purpose: "live", channel: "mcp", mode: "interactive" },
      workspaceDir: repoRoot,
      stateRoot: stateDir,
    };
    const result = await tool.execute(input, ctx);
    return { content: [{ type: "text", text: typeof result === "string" ? result : JSON.stringify(result) }] };
  } catch (err) {
    const message = err instanceof z.ZodError ? `Invalid input: ${err.issues.map((i) => `${i.path.join(".")} ${i.message}`).join("; ")}` : String((err as Error).message ?? err);
    return { isError: true, content: [{ type: "text", text: message }] };
  }
});

await server.connect(new StdioServerTransport());
