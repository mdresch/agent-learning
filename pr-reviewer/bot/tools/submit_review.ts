import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { parsePrUrl } from "../lib/github.js";

export default defineTool({
  description: "Approve the pull request, or comment asking for a human review.",
  effect: "write",
  inputSchema: z.object({
    prUrl: z.string().describe("GitHub pull request URL"),
    verdict: z.enum(["approve", "request_human_review"]),
    summary: z.string().describe("One or two sentences on why."),
  }),
  async execute({ prUrl, verdict, summary }, ctx) {
    if (ctx.session.purpose === "eval") {
      return { posted: true, verdict };
    }
    const approve = verdict === "approve";
    const octokit = await ctx.host.github.getOctokit();
    await octokit.rest.pulls.createReview({
      ...parsePrUrl(prUrl),
      event: approve ? "APPROVE" : "COMMENT",
      body: approve ? summary : `Human review needed. ${summary}`,
    });
    return { posted: true, verdict };
  },
});