import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { evalPull } from "../lib/eval-fixtures.js";
import { parsePrUrl } from "../lib/github.js";

function rateComplexity(linesChanged: number, changedFiles: number) {
  if (linesChanged <= 25 && changedFiles <= 2) {
    return "trivial";
  }
  if (linesChanged <= 400 && changedFiles <= 15) {
    return "moderate";
  }
  return "large";
}

export default defineTool({
  description: "Fetch a pull request's title, patches, and complexity.",
  effect: "read",
  inputSchema: z.object({ prUrl: z.string().describe("GitHub pull request URL") }),
  async execute({ prUrl }, ctx) {
    if (ctx.session.purpose === "eval") {
      const fixture = evalPull(prUrl);
      if (fixture === undefined) {
        throw new Error(`No eval fixture for ${prUrl}`);
      }
      const linesChanged = fixture.files.reduce(
        (sum, file) => sum + file.additions + file.deletions,
        0,
      );
      const complexity = rateComplexity(linesChanged, fixture.files.length);
      return {
        title: fixture.title,
        draft: fixture.draft,
        complexity,
        files: fixture.files.map((file) => ({
          path: file.path,
          additions: file.additions,
          deletions: file.deletions,
          patch: complexity === "large" ? undefined : file.patch,
        })),
      };
    }
    const pull = parsePrUrl(prUrl);
    const octokit = await ctx.host.github.getOctokit();
    const { data: pr } = await octokit.rest.pulls.get(pull);
    const files = await octokit.paginate(octokit.rest.pulls.listFiles, {
      ...pull,
      per_page: 100,
    });
    const complexity = rateComplexity(pr.additions + pr.deletions, pr.changed_files);

    return {
      title: pr.title,
      draft: pr.draft ?? false,
      complexity,
      files: files.map((file) => ({
        path: file.filename,
        additions: file.additions,
        deletions: file.deletions,
        patch: complexity === "large" ? undefined : file.patch?.slice(0, 3000),
      })),
    };
  },
});