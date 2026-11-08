import { defineAgent } from "@grok/agent-sdk";

// Read-only file tools plus delegation. There is deliberately no "shell" and no "edit":
//   - writes go through write_document (per-stage path allowlist, frozen baselines)
//   - commands go through run_command (read-only allowlist, no gate adjudication)
//   - the approval secret stays unreachable, so the agent cannot forge a human decision
// Do not add "shell" or "edit" without revisiting that boundary.
export default defineAgent({
  model: {
    id: "grok-4.7",
    params: [
      { id: "reasoning_effort", value: "high" },
      { id: "fast", value: "true" },
    ],
  },
  local: {
    workspaceDir: "..",
  },
  tools: ["read", "grep", "glob", "ls", "task"],
});
