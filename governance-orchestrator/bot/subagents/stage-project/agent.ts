import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Stage 7 Project (PMP & Baselines): checks the subsidiary management plans and the PMP baseline. Never writes plans; they come from the pmbok-planning tooling. Recommends a verdict; does not approve.",
});
