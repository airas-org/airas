"use client";

import { ChevronDown, ChevronUp } from "lucide-react";
import { type ReactNode, useMemo, useState } from "react";
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
        (item): item is string => typeof item === "string" && item.trim(),
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

const Section = ({ title, children }: { title: string; children: ReactNode }) => (
  <div className="rounded-md border border-border bg-card/60">
    <div className="border-b border-border/50 px-3 py-2 text-sm font-semibold text-foreground">
      {title}
    </div>
    <div className="p-3 space-y-2 text-sm text-foreground">{children}</div>
  </div>
);

interface ToggleSectionProps {
  title: string;
  isOpen: boolean;
  onToggle: () => void;
  children: ReactNode;
}

const ToggleSection = ({ title, isOpen, onToggle, children }: ToggleSectionProps) => (
  <div className="rounded-md border border-border bg-card/60">
    <button
      type="button"
      className="flex w-full items-center justify-between px-3 py-2 text-left text-sm font-semibold text-foreground"
      onClick={onToggle}
    >
      <span>{title}</span>
      {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
    </button>
    {isOpen && <div className="border-t border-border/50 p-3 space-y-2 text-sm">{children}</div>}
  </div>
);

const Description = ({ text }: { text?: string | null }) => {
  if (!text) return null;
  return <p className="whitespace-pre-wrap text-muted-foreground">{text}</p>;
};

const BulletList = ({ items }: { items?: string[] | null }) => {
  if (!items?.length) return null;
  return (
    <ul className="list-inside list-disc space-y-1 text-muted-foreground">
      {items.map((item) => (
        <li key={item} className="break-words">
          {item}
        </li>
      ))}
    </ul>
  );
};

const MetricsList = ({
  metrics,
}: {
  metrics?: ExperimentalDesign_Output["evaluation_metrics"];
}) => {
  if (!metrics?.length) return null;
  return (
    <div className="space-y-2">
      {metrics.map((metric) => {
        const key = metric.name || metric.description || JSON.stringify(metric);
        return (
          <div key={key} className="rounded border border-border/50 bg-background/60 p-2">
            <p className="text-sm font-semibold text-foreground">評価指標: {metric.name}</p>
            <Description text={metric.description} />
          </div>
        );
      })}
    </div>
  );
};

const ComparativeMethods = ({
  methods,
}: {
  methods?: ExperimentalDesign_Output["comparative_methods"];
}) => {
  if (!methods?.length) return null;
  return (
    <div className="space-y-2">
      {methods.map((method) => (
        <div
          key={method.method_name || method.description || JSON.stringify(method)}
          className="rounded border border-border/50 bg-background/60 p-2"
        >
          <p className="text-sm font-semibold text-foreground">
            ベースライン: {method.method_name}
          </p>
          <Description text={method.description} />
        </div>
      ))}
    </div>
  );
};

const ProposedMethod = ({ method }: { method?: ExperimentalDesign_Output["proposed_method"] }) => {
  if (!method) return null;
  return (
    <div className="space-y-1">
      <p className="text-sm font-semibold text-foreground">{method.method_name}</p>
      <Description text={method.description} />
    </div>
  );
};

const MetricsData = ({ data }: { data?: Record<string, unknown> | null }) => {
  if (!data || Object.keys(data).length === 0) return null;
  return (
    <pre className="max-h-80 overflow-auto rounded border border-border/50 bg-background/60 p-3 text-xs text-muted-foreground">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
};

export function AutoResearchResultDisplay({ snapshot }: { snapshot: AutoResearchResultSnapshot }) {
  const [openSections, setOpenSections] = useState({
    researchHypothesis: true,
    experimentalDesign: true,
    experimentalResults: true,
    paperContent: true,
  });

  const hasAny = useMemo(
    () =>
      Boolean(
        snapshot.research_topic ||
          snapshot.queries?.length ||
          snapshot.paper_titles?.length ||
          snapshot.research_hypothesis ||
          snapshot.experimental_design ||
          snapshot.github_url ||
          snapshot.experimental_results ||
          snapshot.experimental_analysis ||
          snapshot.paper_content,
      ),
    [snapshot],
  );

  if (!hasAny) {
    return <p className="text-sm text-muted-foreground">まだ表示できる進捗はありません。</p>;
  }

  return (
    <div className="space-y-3">
      {snapshot.research_topic && (
        <Section title="research_topic">
          <p className="text-foreground whitespace-pre-wrap">{snapshot.research_topic}</p>
        </Section>
      )}

      {snapshot.queries?.length ? (
        <Section title="queries">
          <BulletList items={snapshot.queries} />
        </Section>
      ) : null}

      {snapshot.paper_titles?.length ? (
        <Section title="paper_titles">
          <BulletList items={snapshot.paper_titles} />
        </Section>
      ) : null}

      {snapshot.research_hypothesis && (
        <ToggleSection
          title="research_hypothesis"
          isOpen={openSections.researchHypothesis}
          onToggle={() =>
            setOpenSections((prev) => ({ ...prev, researchHypothesis: !prev.researchHypothesis }))
          }
        >
          <div className="space-y-2">
            <div>
              <p className="font-semibold text-foreground">open_problems</p>
              <Description text={snapshot.research_hypothesis.open_problems} />
            </div>
            <div>
              <p className="font-semibold text-foreground">method</p>
              <Description text={snapshot.research_hypothesis.method} />
            </div>
            <div>
              <p className="font-semibold text-foreground">primary_metric</p>
              <Description text={snapshot.research_hypothesis.primary_metric} />
            </div>
            <div>
              <p className="font-semibold text-foreground">expected_result</p>
              <Description text={snapshot.research_hypothesis.expected_result} />
            </div>
            <div>
              <p className="font-semibold text-foreground">experimental_setup</p>
              <Description text={snapshot.research_hypothesis.experimental_setup} />
            </div>
            <div>
              <p className="font-semibold text-foreground">expected_conclusion</p>
              <Description text={snapshot.research_hypothesis.expected_conclusion} />
            </div>
          </div>
        </ToggleSection>
      )}

      {snapshot.experimental_design && (
        <ToggleSection
          title="experimental_design"
          isOpen={openSections.experimentalDesign}
          onToggle={() =>
            setOpenSections((prev) => ({ ...prev, experimentalDesign: !prev.experimentalDesign }))
          }
        >
          <div className="space-y-3">
            <div>
              <p className="font-semibold text-foreground">experiment_summary</p>
              <Description text={snapshot.experimental_design.experiment_summary} />
            </div>
            <div>
              <p className="font-semibold text-foreground">evaluation_metrics</p>
              <MetricsList metrics={snapshot.experimental_design.evaluation_metrics} />
            </div>
            <div>
              <p className="font-semibold text-foreground">models_to_use</p>
              <BulletList items={snapshot.experimental_design.models_to_use} />
            </div>
            <div>
              <p className="font-semibold text-foreground">datasets_to_use</p>
              <BulletList items={snapshot.experimental_design.datasets_to_use} />
            </div>
            <div>
              <p className="font-semibold text-foreground">proposed_method</p>
              <ProposedMethod method={snapshot.experimental_design.proposed_method} />
            </div>
            <div>
              <p className="font-semibold text-foreground">comparative_methods</p>
              <ComparativeMethods methods={snapshot.experimental_design.comparative_methods} />
            </div>
          </div>
        </ToggleSection>
      )}

      {snapshot.github_url && (
        <Section title="github_url">
          <a
            href={snapshot.github_url}
            target="_blank"
            rel="noreferrer"
            className="text-primary underline break-all"
          >
            {snapshot.github_url}
          </a>
        </Section>
      )}

      {snapshot.experimental_results && (
        <ToggleSection
          title="experimental_results"
          isOpen={openSections.experimentalResults}
          onToggle={() =>
            setOpenSections((prev) => ({
              ...prev,
              experimentalResults: !prev.experimentalResults,
            }))
          }
        >
          <div className="space-y-3">
            {snapshot.experimental_results.stdout && (
              <div>
                <p className="font-semibold text-foreground">stdout</p>
                <Description text={snapshot.experimental_results.stdout} />
              </div>
            )}
            {snapshot.experimental_results.stderr && (
              <div>
                <p className="font-semibold text-foreground">stderr</p>
                <Description text={snapshot.experimental_results.stderr} />
              </div>
            )}
            <div>
              <p className="font-semibold text-foreground">metrics_data</p>
              <MetricsData data={snapshot.experimental_results.metrics_data ?? undefined} />
            </div>
          </div>
        </ToggleSection>
      )}

      {snapshot.experimental_analysis && (
        <Section title="experimental_analysis">
          <Description text={snapshot.experimental_analysis.analysis_report} />
        </Section>
      )}

      {snapshot.paper_content && (
        <ToggleSection
          title="paper_content"
          isOpen={openSections.paperContent}
          onToggle={() =>
            setOpenSections((prev) => ({ ...prev, paperContent: !prev.paperContent }))
          }
        >
          <div className="space-y-2">
            <div>
              <p className="font-semibold text-foreground">title</p>
              <Description text={snapshot.paper_content.title} />
            </div>
            <div>
              <p className="font-semibold text-foreground">abstract</p>
              <Description text={snapshot.paper_content.abstract} />
            </div>
            <div>
              <p className="font-semibold text-foreground">introduction</p>
              <Description text={snapshot.paper_content.introduction} />
            </div>
            <div>
              <p className="font-semibold text-foreground">related_work</p>
              <Description text={snapshot.paper_content.related_work} />
            </div>
            <div>
              <p className="font-semibold text-foreground">background</p>
              <Description text={snapshot.paper_content.background} />
            </div>
            <div>
              <p className="font-semibold text-foreground">method</p>
              <Description text={snapshot.paper_content.method} />
            </div>
            <div>
              <p className="font-semibold text-foreground">experimental_setup</p>
              <Description text={snapshot.paper_content.experimental_setup} />
            </div>
            <div>
              <p className="font-semibold text-foreground">results</p>
              <Description text={snapshot.paper_content.results} />
            </div>
            <div>
              <p className="font-semibold text-foreground">conclusion</p>
              <Description text={snapshot.paper_content.conclusion} />
            </div>
          </div>
        </ToggleSection>
      )}
    </div>
  );
}
