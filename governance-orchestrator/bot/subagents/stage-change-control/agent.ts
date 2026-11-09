import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Stages 16 Governance Change and 17 Adaptation Plan: classifies a candidate diff against the frozen baseline, prepares the escalation decision, and reviews the Adaptation Plan. Does not apply any governance change or approve.",
});
