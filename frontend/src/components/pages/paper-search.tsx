import { FeatherAlertTriangle, FeatherExternalLink } from "@subframe/core";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { PaperSearchResult } from "@/lib/api/models/PaperSearchResult";
import { SearchPapersRequestBody } from "@/lib/api/models/SearchPapersRequestBody";
import { CredentialsService } from "@/lib/api/services/CredentialsService";
import { PapersService } from "@/lib/api/services/PapersService";
import { Alert } from "@/ui/components/Alert";
import { Badge } from "@/ui/components/Badge";
import { Button } from "@/ui/components/Button";
import { Checkbox } from "@/ui/components/Checkbox";
import { TextField } from "@/ui/components/TextField";

const ALL_SOURCES = ["openalex", "semantic_scholar", "arxiv", "airas_db"] as const;
// Sources that support semantic (AI-embedding) search, and the credential each needs.
const SEMANTIC_SOURCES = ["openalex"] as const;
const SEMANTIC_KEY = "OPENALEX_API_KEY";

type SearchMode = SearchPapersRequestBody.search_mode;
const SEARCH_MODES = [
  SearchPapersRequestBody.search_mode.KEYWORD,
  SearchPapersRequestBody.search_mode.SEMANTIC,
] as const;

type FulltextState =
  | { status: "loading" }
  | { status: "error" }
  | { status: "done"; text: string; fulltextStatus: string };

export function PaperSearchPage() {
  const { t } = useTranslation();
  const [query, setQuery] = useState("");
  const [sources, setSources] = useState<string[]>([...ALL_SOURCES]);
  const [searchMode, setSearchMode] = useState<SearchMode>(
    SearchPapersRequestBody.search_mode.KEYWORD,
  );
  const [year, setYear] = useState("");
  const [maxResults, setMaxResults] = useState("5");
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [papers, setPapers] = useState<PaperSearchResult[] | null>(null);
  const [sourceResults, setSourceResults] = useState<Record<string, number>>({});
  const [searchErrors, setSearchErrors] = useState<Record<string, string>>({});
  const [fulltexts, setFulltexts] = useState<Record<string, FulltextState>>({});
  // null = still loading credential status.
  const [semanticKeySet, setSemanticKeySet] = useState<boolean | null>(null);

  useEffect(() => {
    CredentialsService.listCredentialsAirasV1CredentialsGet()
      .then((res) => {
        const cred = res.credentials.find((c) => c.name === SEMANTIC_KEY);
        setSemanticKeySet(Boolean(cred?.is_set));
      })
      .catch(() => setSemanticKeySet(false));
  }, []);

  // In semantic mode the key must be configured; surface the error immediately.
  const isSemantic = searchMode === SearchPapersRequestBody.search_mode.SEMANTIC;
  const semanticKeyMissing = isSemantic && semanticKeySet === false;

  const switchMode = (mode: SearchMode) => {
    setSearchMode(mode);
    setError(null);
    // Semantic search is OpenAlex-only; restrict the source selection.
    setSources(
      mode === SearchPapersRequestBody.search_mode.SEMANTIC
        ? [...SEMANTIC_SOURCES]
        : [...ALL_SOURCES],
    );
  };

  const toggleSource = (source: string, checked: boolean) => {
    setSources((prev) => (checked ? [...prev, source] : prev.filter((s) => s !== source)));
  };

  const handleSearch = async () => {
    if (!query.trim() || sources.length === 0 || semanticKeyMissing) return;
    setSearching(true);
    setError(null);
    setFulltexts({});
    try {
      const res = await PapersService.searchPapersAirasV1PapersSourceSearchPost({
        query: query.trim(),
        sources,
        max_results_per_source: Number(maxResults) || 5,
        year: year.trim() || null,
        search_mode: searchMode,
      });
      setPapers(res.papers);
      setSourceResults(res.source_results);
      setSearchErrors(res.search_errors);
    } catch {
      setError(t("paperSearch.searchError"));
    } finally {
      setSearching(false);
    }
  };

  const paperKey = (paper: PaperSearchResult, index: number) =>
    paper.doi ?? paper.arxiv_id ?? paper.url ?? `${paper.source}-${index}`;

  const handleFetchFulltext = async (key: string, paper: PaperSearchResult) => {
    setFulltexts((prev) => ({ ...prev, [key]: { status: "loading" } }));
    try {
      const res = await PapersService.fetchPaperFulltextAirasV1PapersFulltextPost({
        arxiv_id: paper.arxiv_id ?? null,
        doi: paper.doi ?? null,
        pdf_url: paper.pdf_url ?? null,
      });
      setFulltexts((prev) => ({
        ...prev,
        [key]: { status: "done", text: res.text, fulltextStatus: res.status },
      }));
    } catch {
      setFulltexts((prev) => ({ ...prev, [key]: { status: "error" } }));
    }
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font">
          {t("paperSearch.pageTitle")}
        </h1>
        <p className="text-caption font-caption text-subtext-color mt-1">
          {t("paperSearch.pageSubtitle")}
        </p>

        {/* Search form */}
        <div className="mt-6 rounded-lg border border-border bg-card p-6 flex flex-col gap-4">
          {/* Mode toggle */}
          <div className="flex items-center gap-2">
            <span className="text-caption-bold font-caption-bold text-default-font">
              {t("paperSearch.mode")}
            </span>
            {SEARCH_MODES.map((mode) => (
              <Button
                key={mode}
                variant={searchMode === mode ? "brand-primary" : "neutral-tertiary"}
                size="small"
                onClick={() => switchMode(mode)}
              >
                {t(`paperSearch.modes.${mode}`)}
              </Button>
            ))}
            {isSemantic && (
              <span className="text-caption font-caption text-subtext-color">
                {t("paperSearch.semanticHint")}
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <TextField className="flex-1" error={false}>
              <TextField.Input
                placeholder={t("paperSearch.queryPlaceholder")}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSearch();
                }}
              />
            </TextField>
            <Button
              onClick={handleSearch}
              disabled={searching || !query.trim() || sources.length === 0 || semanticKeyMissing}
            >
              {searching ? t("paperSearch.searching") : t("paperSearch.search")}
            </Button>
          </div>
          <div className="flex flex-wrap items-center gap-5">
            <span className="text-caption-bold font-caption-bold text-default-font">
              {t("paperSearch.sources")}
            </span>
            {ALL_SOURCES.map((source) => {
              const disabled =
                isSemantic &&
                !SEMANTIC_SOURCES.includes(source as (typeof SEMANTIC_SOURCES)[number]);
              return (
                <Checkbox
                  key={source}
                  label={t(`paperSearch.sourceNames.${source}`)}
                  checked={sources.includes(source)}
                  disabled={disabled}
                  onCheckedChange={(checked) => toggleSource(source, checked)}
                />
              );
            })}
            <div className="flex items-center gap-2 ml-auto">
              <span className="text-caption font-caption text-subtext-color">
                {t("paperSearch.year")}
              </span>
              <TextField className="w-28" error={false}>
                <TextField.Input
                  placeholder="2020-2025"
                  value={year}
                  onChange={(e) => setYear(e.target.value)}
                />
              </TextField>
              <span className="text-caption font-caption text-subtext-color">
                {t("paperSearch.maxResults")}
              </span>
              <TextField className="w-16" error={false}>
                <TextField.Input
                  type="number"
                  value={maxResults}
                  onChange={(e) => setMaxResults(e.target.value)}
                />
              </TextField>
            </div>
          </div>
        </div>

        {semanticKeyMissing && (
          <div className="mt-4">
            <Alert
              variant="error"
              icon={<FeatherAlertTriangle />}
              title={t("paperSearch.semanticKeyMissingTitle")}
              description={t("paperSearch.semanticKeyMissingDescription")}
            />
          </div>
        )}

        {error && (
          <div className="mt-4">
            <Alert variant="error" icon={<FeatherAlertTriangle />} title={error} />
          </div>
        )}

        {/* Per-source stats */}
        {papers !== null && (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-caption font-caption text-subtext-color">
              {t("paperSearch.resultCount", { count: papers.length })}
            </span>
            {Object.entries(sourceResults).map(([source, count]) => (
              <Badge key={source} variant="neutral">
                {t(`paperSearch.sourceNames.${source}`)}: {count}
              </Badge>
            ))}
            {Object.entries(searchErrors).map(([source, message]) => (
              <Badge key={source} variant="error" title={message}>
                {t(`paperSearch.sourceNames.${source}`)}: {t("paperSearch.sourceFailed")}
              </Badge>
            ))}
          </div>
        )}

        {/* Results */}
        <div className="mt-4 flex flex-col gap-4">
          {(papers ?? []).map((paper, index) => {
            const key = paperKey(paper, index);
            const fulltext = fulltexts[key];
            const canFetch = paper.arxiv_id || paper.doi || paper.pdf_url;
            return (
              <div key={key} className="rounded-lg border border-border bg-card p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    {paper.url ? (
                      <a
                        href={paper.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-body-bold font-body-bold text-brand-700 hover:underline inline-flex items-center gap-1"
                      >
                        {paper.title}
                        <FeatherExternalLink className="h-3.5 w-3.5 shrink-0" />
                      </a>
                    ) : (
                      <span className="text-body-bold font-body-bold text-default-font">
                        {paper.title}
                      </span>
                    )}
                    <p className="text-caption font-caption text-subtext-color mt-1">
                      {(paper.authors ?? []).slice(0, 5).join(", ")}
                      {(paper.authors ?? []).length > 5 ? " et al." : ""}
                      {paper.venue ? ` · ${paper.venue}` : ""}
                      {paper.published_date ? ` · ${paper.published_date}` : ""}
                      {paper.citations != null
                        ? ` · ${t("paperSearch.citations", { count: paper.citations })}`
                        : ""}
                    </p>
                  </div>
                  <Badge variant="brand">{t(`paperSearch.sourceNames.${paper.source}`)}</Badge>
                </div>

                {paper.abstract && (
                  <p className="text-caption font-caption text-default-font mt-3 line-clamp-3">
                    {paper.abstract}
                  </p>
                )}

                <div className="mt-3 flex items-center gap-3">
                  {canFetch && !fulltext && (
                    <Button
                      variant="neutral-secondary"
                      size="small"
                      onClick={() => handleFetchFulltext(key, paper)}
                    >
                      {t("paperSearch.fetchFulltext")}
                    </Button>
                  )}
                  {fulltext?.status === "loading" && (
                    <span className="inline-flex items-center gap-2 text-caption font-caption text-subtext-color">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      {t("paperSearch.fetchingFulltext")}
                    </span>
                  )}
                  {fulltext?.status === "error" && (
                    <span className="text-caption font-caption text-error-600">
                      {t("paperSearch.fulltextError")}
                    </span>
                  )}
                </div>

                {fulltext?.status === "done" && (
                  <div className="mt-3">
                    <Badge variant={fulltext.fulltextStatus === "fulltext" ? "success" : "warning"}>
                      {t(`paperSearch.fulltextStatus.${fulltext.fulltextStatus}`)}
                    </Badge>
                    {fulltext.text && (
                      <div className="mt-2 max-h-64 overflow-y-auto rounded-md border border-border bg-default-background p-3">
                        <p className="text-caption font-caption text-default-font whitespace-pre-wrap">
                          {fulltext.text}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
          {papers !== null && papers.length === 0 && (
            <p className="text-body font-body text-subtext-color text-center py-8">
              {t("paperSearch.noResults")}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
