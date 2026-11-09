import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Stages 5 Pillars & Architecture and 6 Requirement: designs the project pillars and reviews ADRs, BRDs, FDDs and user stories against pillar coverage, prior ADRs and technique best practice. Carries the former adr_reviewer rubric. Recommends a verdict; does not approve.",
});
