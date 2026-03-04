import { FeatherSearch } from "@subframe/core";
import { useMemo, useState } from "react";
import { Badge, TextField } from "@/ui";

interface SearchPageProps {
  onNavigate?: (nav: string, id?: string) => void;
}

interface VerificationResult {
  id: string;
  title: string;
  phase: string;
  phaseVariant: "brand" | "neutral" | "warning" | "success" | "error";
  date: string;
}

interface PaperResult {
  id: string;
  title: string;
  authors: string;
  year: string;
}

interface ExperimentResult {
  id: string;
  title: string;
  status: string;
  statusVariant: "brand" | "neutral" | "warning" | "success" | "error";
  metrics: string;
}

const mockVerifications: VerificationResult[] = [
  {
    id: "v1",
    title: "強化学習による最適化手法の比較検証",
    phase: "実験完了",
    phaseVariant: "success",
    date: "2026-03-04",
  },
  {
    id: "v2",
    title: "LLMの推論能力評価フレームワーク",
    phase: "コード生成中",
    phaseVariant: "warning",
    date: "2026-03-03",
  },
  {
    id: "v3",
    title: "画像認識モデルの精度比較",
    phase: "論文生成済み",
    phaseVariant: "brand",
    date: "2026-03-01",
  },
];

const mockPapers: PaperResult[] = [
  {
    id: "p1",
    title: "Comparative Analysis of Reinforcement Learning Optimization Methods",
    authors: "田中太郎, 佐藤花子",
    year: "2026",
  },
  {
    id: "p2",
    title: "A Framework for Evaluating LLM Reasoning Capabilities",
    authors: "鈴木一郎, 山田次郎",
    year: "2026",
  },
];

const mockExperiments: ExperimentResult[] = [
  {
    id: "e1",
    title: "PPO vs DQN ベンチマーク実験",
    status: "完了",
    statusVariant: "success",
    metrics: "精度: 94.2%, 収束エポック: 150",
  },
  {
    id: "e2",
    title: "BERT ファインチューニング実験",
    status: "実行中",
    statusVariant: "warning",
    metrics: "精度: 87.5% (暫定), エポック: 80/200",
  },
];

function matchesQuery(text: string, query: string): boolean {
  return text.toLowerCase().includes(query.toLowerCase());
}

export function SearchPage({ onNavigate }: SearchPageProps) {
  const [query, setQuery] = useState("");

  const filteredVerifications = useMemo(
    () =>
      query
        ? mockVerifications.filter(
            (v) => matchesQuery(v.title, query) || matchesQuery(v.phase, query),
          )
        : mockVerifications,
    [query],
  );

  const filteredPapers = useMemo(
    () =>
      query
        ? mockPapers.filter((p) => matchesQuery(p.title, query) || matchesQuery(p.authors, query))
        : mockPapers,
    [query],
  );

  const filteredExperiments = useMemo(
    () =>
      query
        ? mockExperiments.filter(
            (e) => matchesQuery(e.title, query) || matchesQuery(e.metrics, query),
          )
        : mockExperiments,
    [query],
  );

  const hasResults =
    filteredVerifications.length > 0 || filteredPapers.length > 0 || filteredExperiments.length > 0;

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font mb-6">検索</h1>

        <TextField icon={<FeatherSearch />} className="mb-8">
          <TextField.Input
            placeholder="検証、論文、実験を検索..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </TextField>

        {!hasResults && query && (
          <p className="py-12 text-center text-body font-body text-subtext-color">
            検索結果が見つかりませんでした
          </p>
        )}

        {hasResults && (
          <div className="flex flex-col gap-8">
            {filteredVerifications.length > 0 && (
              <section>
                <h2 className="text-body-bold font-body-bold text-default-font mb-3">
                  検証
                  <span className="ml-2 text-caption font-caption text-subtext-color">
                    {filteredVerifications.length}件
                  </span>
                </h2>
                <div className="flex flex-col gap-2">
                  {filteredVerifications.map((v) => (
                    <button
                      key={v.id}
                      type="button"
                      className="flex items-center justify-between rounded-lg border border-border bg-card p-4 text-left hover:bg-neutral-50 transition-colors"
                      onClick={() => onNavigate?.("verification", v.id)}
                    >
                      <div className="flex-1 min-w-0">
                        <span className="text-body-bold font-body-bold text-default-font">
                          {v.title}
                        </span>
                        <span className="text-caption font-caption text-subtext-color ml-3">
                          {v.date}
                        </span>
                      </div>
                      <Badge variant={v.phaseVariant}>{v.phase}</Badge>
                    </button>
                  ))}
                </div>
              </section>
            )}

            {filteredPapers.length > 0 && (
              <section>
                <h2 className="text-body-bold font-body-bold text-default-font mb-3">
                  論文
                  <span className="ml-2 text-caption font-caption text-subtext-color">
                    {filteredPapers.length}件
                  </span>
                </h2>
                <div className="flex flex-col gap-2">
                  {filteredPapers.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      className="flex items-center justify-between rounded-lg border border-border bg-card p-4 text-left hover:bg-neutral-50 transition-colors"
                      onClick={() => onNavigate?.("paper", p.id)}
                    >
                      <div className="flex-1 min-w-0">
                        <span className="text-body-bold font-body-bold text-default-font">
                          {p.title}
                        </span>
                        <p className="text-caption font-caption text-subtext-color mt-1">
                          {p.authors} ({p.year})
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              </section>
            )}

            {filteredExperiments.length > 0 && (
              <section>
                <h2 className="text-body-bold font-body-bold text-default-font mb-3">
                  実験
                  <span className="ml-2 text-caption font-caption text-subtext-color">
                    {filteredExperiments.length}件
                  </span>
                </h2>
                <div className="flex flex-col gap-2">
                  {filteredExperiments.map((e) => (
                    <button
                      key={e.id}
                      type="button"
                      className="flex items-center justify-between rounded-lg border border-border bg-card p-4 text-left hover:bg-neutral-50 transition-colors"
                      onClick={() => onNavigate?.("experiment", e.id)}
                    >
                      <div className="flex-1 min-w-0">
                        <span className="text-body-bold font-body-bold text-default-font">
                          {e.title}
                        </span>
                        <p className="text-caption font-caption text-subtext-color mt-1">
                          {e.metrics}
                        </p>
                      </div>
                      <Badge variant={e.statusVariant}>{e.status}</Badge>
                    </button>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
