import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Stage 9 Deliverable: prepares the implement-story hand-off, inspects existing branches and worktrees read-only, and rates PR complexity. Carries the former pr-reviewer rubric as a recommendation only. Never writes code, approves or merges.",
});
