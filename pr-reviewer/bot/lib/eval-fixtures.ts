export type EvalFile = {
  path: string;
  additions: number;
  deletions: number;
  patch?: string;
};

export type EvalPull = {
  title: string;
  draft: boolean;
  files: EvalFile[];
};

const pulls: Record<string, EvalPull> = {
  "https://github.com/example/repo/pull/42": {
    title: "Fix a typo in the readme",
    draft: false,
    files: [
      {
        path: "README.md",
        additions: 1,
        deletions: 1,
        patch: "@@\n-recieve\n+receive\n",
      },
    ],
  },
  "https://github.com/example/repo/pull/7": {
    title: "Rewrite the billing pipeline",
    draft: false,
    files: [
      { path: "src/billing/pipeline.ts", additions: 500, deletions: 80 },
      ...Array.from({ length: 19 }, (_, index) => ({
        path: `src/billing/part-${index}.ts`,
        additions: 10,
        deletions: 2,
      })),
    ],
  },
  "https://github.com/example/repo/pull/3": {
    title: "Fix a typo in the readme",
    draft: true,
    files: [
      {
        path: "README.md",
        additions: 1,
        deletions: 1,
        patch: "@@\n-recieve\n+receive\n",
      },
    ],
  },
};

export function evalPull(prUrl: string): EvalPull | undefined {
  return pulls[prUrl];
}
