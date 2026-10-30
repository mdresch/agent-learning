import { defineEval } from "@grok/agent-sdk/evals";

const trivial = "https://github.com/example/repo/pull/42";
const large = "https://github.com/example/repo/pull/7";
const draft = "https://github.com/example/repo/pull/3";

export default defineEval({
  tags: ["review"],
  cases: [
    {
      id: "trivial",
      description: "A one-line readme fix is approved after inspection.",
      async test(t) {
        await t.send(`Review ${trivial}.`);
        t.succeeded();
        t.toolOrder(["inspect_pr", "submit_review"]);
        t.calledTool("inspect_pr", { input: { prUrl: trivial }, count: 1 });
        t.calledTool("submit_review", {
          input: { prUrl: trivial, verdict: "approve" },
          count: 1,
        });
      },
    },
    {
      id: "large",
      description: "A large change is sent to a human reviewer.",
      async test(t) {
        await t.send(`Review ${large}.`);
        t.succeeded();
        t.toolOrder(["inspect_pr", "submit_review"]);
        t.calledTool("inspect_pr", { input: { prUrl: large }, count: 1 });
        t.calledTool("submit_review", {
          input: { prUrl: large, verdict: "request_human_review" },
          count: 1,
        });
      },
    },
    {
      id: "draft",
      description: "A draft is not approved, even when the diff is trivial.",
      async test(t) {
        await t.send(`Review ${draft}.`);
        t.succeeded();
        t.toolOrder(["inspect_pr", "submit_review"]);
        t.calledTool("inspect_pr", { input: { prUrl: draft }, count: 1 });
        t.calledTool("submit_review", {
          input: { prUrl: draft, verdict: "request_human_review" },
          count: 1,
        });
      },
    },
  ],
});
