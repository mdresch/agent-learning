import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Designs the project pillars from the spark, ideation, business case, and value statement, and writes docs/project-docs/Project-Pillars.md. Use when the user asks to design or refresh the pillars. Do not use during an ADR verdict.",
});
