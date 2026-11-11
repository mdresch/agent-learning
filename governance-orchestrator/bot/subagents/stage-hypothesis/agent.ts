import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Stage 3 Hypothesis: evaluates each HYP-* entry in the Ideation Document against its evidence and reports a classification recommendation to the orchestrator. Does not approve.",
});
