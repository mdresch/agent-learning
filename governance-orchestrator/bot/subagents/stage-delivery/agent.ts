import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Stages 9 Deliverable and 10 Verification Evidence: prepares the implement-story hand-off, inspects existing branches and worktrees read-only, verifies test evidence, and rates PR complexity. Carries the former pr-reviewer rubric as a recommendation only. Never writes code, approves or merges.",
});
