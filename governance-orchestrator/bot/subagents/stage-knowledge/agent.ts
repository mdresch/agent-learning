import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Stages 14 Insight and 15 Lesson Learned: synthesizes observations into insights and drafts Lessons Learned and Continuous Improvement register entries for a human to accept. Does not accept entries or create resolve-kb-conflict episodes.",
});
