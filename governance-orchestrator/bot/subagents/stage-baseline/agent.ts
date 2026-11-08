import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Stages 7 Project (subsidiary plans and PMP baseline) and 8 Implementation Readiness: checks plans and the readiness gate. Never writes plans; they come from the pmbok-planning tooling. Recommends a verdict; does not approve.",
});
