import type { ResearchStudy, RetrievePaperSubgraphResponseBody } from "@/lib/api";
import type { Paper } from "@/types/research";

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://127.0.0.1:8000";
const DEFAULT_MAX_RESULTS_PER_QUERY = 2;

export async function searchPapers(query: string): Promise<Paper[]> {
  const response = await fetch(`${API_BASE_URL}/airas/v1/papers`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query_list: [query],
      max_results_per_query: DEFAULT_MAX_RESULTS_PER_QUERY,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `Failed to retrieve papers: ${response.status} ${errorText || response.statusText}`,
    );
  }

  const data = (await response.json()) as RetrievePaperSubgraphResponseBody;
  const studies = data.research_study_list?.flat() ?? [];

  return studies.map((study, index) => mapStudyToPaper(study, index));
}

function mapStudyToPaper(study: ResearchStudy, index: number): Paper {
  const meta = study.meta_data ?? {};
  const year = parseYear(meta.published_date);
  const authors = (meta.authors ?? []).filter((author) => author && author.trim().length > 0);
  const abstract =
    study.llm_extracted_info?.main_contributions ??
    study.llm_extracted_info?.methodology ??
    study.full_text?.slice(0, 280) ??
    "概要が見つかりません";

  return {
    id: meta.arxiv_id ?? meta.doi ?? `${study.title}-${index}`,
    title: study.title,
    authors: authors.length > 0 ? authors : ["Unknown"],
    abstract,
    year,
    citations: meta.citation_count ?? meta.reference_count ?? 0,
    relevanceScore: clampScore(meta.h_index_relevance ?? 1),
  };
}

function parseYear(dateString?: string | null): number {
  if (!dateString) return new Date().getFullYear();
  const parsed = Number.parseInt(dateString.slice(0, 4), 10);
  return Number.isFinite(parsed) ? parsed : new Date().getFullYear();
}

function clampScore(value?: number | null): number {
  if (value === null || value === undefined) return 1;
  if (Number.isNaN(value)) return 1;
  return Math.max(0, Math.min(1, value));
}
