import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Reads docs/project-docs/Project-Pillars.md and reports the one primary topic pillar named for an ADR in the Primary assignment table. If that file is missing, reply Pillars: missing. Do not invent pillars from the spark, ideation, business case, or value statement. Use on every ADR review. Do not use for the verdict.",
});
