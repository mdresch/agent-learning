export function parsePrUrl(prUrl: string) {
    const [owner, repo, pulls, number] = new URL(prUrl).pathname.split("/").filter(Boolean);
    const pull_number = Number.parseInt(number ?? "", 10);
    if (pulls !== "pull" || owner === undefined || repo === undefined || Number.isNaN(pull_number)) {
      throw new Error(`Not a pull request URL: ${prUrl}`);
    }
    return { owner, repo, pull_number };
  }