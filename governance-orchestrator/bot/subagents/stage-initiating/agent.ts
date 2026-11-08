import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Stages 1 Intent, 3 Hypothesis, 4 Benefit and 2 Objective: Spark Capture, Ideation Document, Business Case, Benefits plan and Project Charter. Reviews or drafts them against the stage requirements and reports to the orchestrator. Does not approve.",
});
