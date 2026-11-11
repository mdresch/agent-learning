import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Stage 6 Requirement: reviews ADRs, BRDs, FDDs and user stories against pillar coverage, prior ADRs and technique best practice, one epic at a time. Carries the former adr_reviewer rubric. Recommends a verdict; does not approve.",
});
