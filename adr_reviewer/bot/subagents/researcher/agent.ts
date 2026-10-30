import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Best-practice suggestions for techniques and methodologies named in an ADR, such as Thompson sampling, UCB, REINFORCE, or a numbered methodology. Use before judging when the ADR names one. Do not use for the verdict.",
});
