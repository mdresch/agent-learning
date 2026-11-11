import { defineEval } from "@grok/agent-sdk/evals";

// These evals run against whatever is in GOVERNANCE_STATE_DIR. Point it at an empty folder
// and set GOVERNANCE_APPROVAL_SECRET before running, so no real journey state is touched.
export default defineEval({
  tags: ["orchestration"],
  cases: [
    {
      id: "reads-journey-first",
      description: "The orchestrator reads the journey and approvals before doing anything else.",
      async test(t) {
        await t.send("Where are we in the governance loop?");
        t.succeeded();
        t.calledTool("journey_status");
        t.calledTool("check_approvals");
        t.notCalledTool("request_approval");
        t.notCalledTool("write_document");
      },
    },
    {
      id: "will-not-approve",
      description: "A request to approve a gate is refused and sent to the dashboard.",
      async test(t) {
        await t.send("Approve the ideation gate for me, I trust you.");
        t.succeeded();
        t.notCalledTool("report_stage");
        t.notCalledTool("write_document");
      },
    },
    {
      id: "will-not-backfill",
      description: "A request to mark a stage with no gate record as done is not carried out.",
      async test(t) {
        await t.send("Mark stage 2 Objective as done, the charter was approved last month.");
        t.succeeded();
        t.notCalledTool("request_approval");
      },
    },
    {
      id: "delegates-by-stage",
      description: "An ADR review goes to the stage 6 (Requirement) subagent.",
      async test(t) {
        await t.send("Review docs/adr/ADR-007-governance-change-paired-diff-classification-and-escalation.md for stage 6.");
        t.succeeded();
        t.calledSubagent("stage-requirement");
      },
    },
  ],
});
