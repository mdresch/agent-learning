import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Stage 10 Verification Evidence: runs the story's contract test and the full suite, and reports the real pass/fail counts. Never edits a test or fixes code.",
});
