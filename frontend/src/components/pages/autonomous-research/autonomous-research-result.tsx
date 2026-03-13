import type {
  ExperimentalAnalysis,
  ExperimentalDesign_Output,
  ExperimentalResults,
  PaperContent,
  ResearchHypothesis,
} from "@/lib/api";

export type AutoResearchResultSnapshot = {
  research_topic?: string;
  queries?: string[];
  paper_titles?: string[];
  research_hypothesis?: ResearchHypothesis;
  experimental_design?: ExperimentalDesign_Output;
  github_url?: string;
  experimental_results?: ExperimentalResults;
  experimental_analysis?: ExperimentalAnalysis;
  paper_content?: PaperContent;
};

export const mergeAutoResearchResultSnapshot = (
  prev: AutoResearchResultSnapshot,
  result: Record<string, unknown> | undefined | null,
  githubUrlFromStatus?: string | null,
): AutoResearchResultSnapshot => {
  if (!result && !githubUrlFromStatus) return prev;

  let updated = false;
  const next: AutoResearchResultSnapshot = { ...prev };

  const assignString = (key: keyof AutoResearchResultSnapshot, value: unknown) => {
    if (next[key] !== undefined) return;
    if (typeof value === "string" && value.trim()) {
      next[key] = value as never;
      updated = true;
    }
  };

  const assignArray = (key: keyof AutoResearchResultSnapshot, value: unknown) => {
    if (next[key] !== undefined) return;
    if (Array.isArray(value)) {
      const strings = value.filter(
        (item): item is string => typeof item === "string" && item.trim().length > 0,
      );
      if (strings.length) {
        next[key] = strings as never;
        updated = true;
      }
    }
  };

  assignString("research_topic", result?.research_topic);
  assignArray("queries", result?.queries);
  assignArray("paper_titles", result?.paper_titles);

  if (next.research_hypothesis === undefined && result?.research_hypothesis) {
    next.research_hypothesis = result.research_hypothesis as ResearchHypothesis;
    updated = true;
  }

  if (next.experimental_design === undefined && result?.experimental_design) {
    next.experimental_design = result.experimental_design as ExperimentalDesign_Output;
    updated = true;
  }

  if (next.experimental_results === undefined && result?.experimental_results) {
    next.experimental_results = result.experimental_results as ExperimentalResults;
    updated = true;
  }

  if (next.experimental_analysis === undefined && result?.experimental_analysis) {
    next.experimental_analysis = result.experimental_analysis as ExperimentalAnalysis;
    updated = true;
  }

  if (next.paper_content === undefined && result?.paper_content) {
    next.paper_content = result.paper_content as PaperContent;
    updated = true;
  }

  if (next.github_url === undefined) {
    const url =
      (typeof result?.github_url === "string" && result.github_url) ||
      (githubUrlFromStatus ?? undefined);
    if (url) {
      next.github_url = url;
      updated = true;
    }
  }

  return updated ? next : prev;
};
