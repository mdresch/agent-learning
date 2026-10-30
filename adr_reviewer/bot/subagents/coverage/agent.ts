import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Reads the spark, ideation, business case, and value statement, names the project pillars those documents use, and links an ADR to the pillars it addresses. Use on every ADR review. Do not use for the verdict.",
});
