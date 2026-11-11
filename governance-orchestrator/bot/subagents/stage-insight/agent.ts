import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Stage 14 Insight: synthesizes observations into insights, each citing the observations it rests on, for a human to accept. Does not accept entries or create resolve-kb-conflict episodes.",
});
