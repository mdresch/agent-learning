import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Stage 16 Governance Change: classifies a candidate diff against the frozen baseline and prepares the escalation decision. Does not apply any governance change or approve.",
});
