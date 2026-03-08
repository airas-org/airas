"use client";

import {
  FeatherArrowLeft,
  FeatherBarChart3,
  FeatherBookOpen,
  FeatherCheck,
  FeatherChevronDown,
  FeatherChevronUp,
  FeatherClipboard,
  FeatherEdit2,
  FeatherExternalLink,
  FeatherFileText,
  FeatherFlaskConical,
  FeatherGithub,
  FeatherLightbulb,
  FeatherLoader,
  FeatherRefreshCw,
  FeatherSearch,
  FeatherTerminal,
  FeatherX,
} from "@subframe/core";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Status,
  TopicOpenEndedResearchService,
  type TopicOpenEndedResearchStatusResponseBody,
} from "@/lib/api";
import type { ResearchSection } from "@/types/research";
import { Badge } from "@/ui/components/Badge";
import { Button } from "@/ui/components/Button";
import { IconButton } from "@/ui/components/IconButton";
import { LinkButton } from "@/ui/components/LinkButton";
import { TextField } from "@/ui/components/TextField";
import {
  type AutoResearchResultSnapshot,
  mergeAutoResearchResultSnapshot,
} from "./autonomous-research-result";

const AUTO_STATUS_POLL_INTERVAL_MS = 5000;

interface TopicDrivenDetailProps {
  section: ResearchSection;
  onBack: () => void;
  onUpdateSectionTitle: (title: string) => void;
  onRefreshSessions: (preferredId?: string) => Promise<void>;
}

export function TopicDrivenDetail({
  section,
  onBack,
  onUpdateSectionTitle,
  onRefreshSessions,
}: TopicDrivenDetailProps) {
  const { t } = useTranslation();
  const [status, setStatus] = useState<TopicOpenEndedResearchStatusResponseBody | null>(null);
  const [resultSnapshot, setResultSnapshot] = useState<AutoResearchResultSnapshot>({});
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [_isRunning, setIsRunning] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isUpdatingTitle, setIsUpdatingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState(section.title);

  const [openSections, setOpenSections] = useState({
    researchHypothesis: true,
    experimentalDesign: true,
    experimentalResults: true,
    paperContent: true,
  });

  const toggleSection = (key: keyof typeof openSections) => {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  useEffect(() => {
    setTitleDraft(section.title);
  }, [section.title]);

  const clearPollingTimer = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const stopPolling = useCallback(() => {
    clearPollingTimer();
    setIsPolling(false);
    setIsRunning(false);
  }, [clearPollingTimer]);

  useEffect(() => () => clearPollingTimer(), [clearPollingTimer]);

  const fetchStatus = useCallback(
    async (taskId: string, { resetError = false } = {}) => {
      if (resetError) setError(null);
      try {
        const response =
          await TopicOpenEndedResearchService.getTopicOpenEndedResearchStatusAirasV1TopicOpenEndedResearchStatusTaskIdGet(
            taskId,
          );
        setStatus(response);
        if (response.error) setError(response.error);
        const finished = response.status === Status.COMPLETED || Boolean(response.error);
        if (finished) stopPolling();
      } catch (err) {
        const message =
          err instanceof Error ? err.message : t("autonomous.topicDriven.statusFetchError");
        setError(message);
        stopPolling();
      }
    },
    [stopPolling, t],
  );

  useEffect(() => {
    if (!status) return;
    setResultSnapshot((prev) =>
      mergeAutoResearchResultSnapshot(prev, status.result, status.github_url),
    );
  }, [status]);

  // Start polling on mount
  useEffect(() => {
    setStatus(null);
    setResultSnapshot({});
    setError(null);
    setIsRunning(true);
    setIsPolling(true);

    void fetchStatus(section.id, { resetError: true });
    pollingRef.current = setInterval(() => {
      void fetchStatus(section.id);
    }, AUTO_STATUS_POLL_INTERVAL_MS);

    return () => clearPollingTimer();
  }, [section.id, fetchStatus, clearPollingTimer]);

  const handleSaveTitle = async () => {
    setIsUpdatingTitle(true);
    setError(null);
    try {
      const updated =
        await TopicOpenEndedResearchService.updateTopicOpenEndedResearchAirasV1TopicOpenEndedResearchTaskIdPatch(
          section.id,
          { title: titleDraft },
        );
      setTitleDraft(updated.title);
      onUpdateSectionTitle(updated.title);
      setIsEditingTitle(false);
      await onRefreshSessions(updated.id);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : t("autonomous.topicDriven.titleUpdateError");
      setError(message);
    } finally {
      setIsUpdatingTitle(false);
    }
  };

  const statusBadge = () => {
    if (!status) return null;
    if (status.status === Status.COMPLETED) {
      return (
        <Badge variant="success" icon={<FeatherCheck />}>
          {t("autonomous.topicDriven.statusCompleted")}
        </Badge>
      );
    }
    if (status.error) {
      return (
        <Badge variant="error" icon={<FeatherX />}>
          {t("autonomous.topicDriven.statusFailed")}
        </Badge>
      );
    }
    return (
      <Badge variant="brand" icon={<FeatherLoader />}>
        {t("autonomous.topicDriven.statusRunning")}
      </Badge>
    );
  };

  const snapshot = resultSnapshot;

  return (
    <div className="flex h-full w-full flex-col items-start bg-default-background">
      <div className="flex w-full flex-col border-b border-solid border-neutral-border bg-default-background px-6 pt-1 pb-2 sticky top-0 z-10 gap-1">
        <div className="flex w-full items-center justify-between">
          <LinkButton variant="neutral" icon={<FeatherArrowLeft />} onClick={onBack}>
            <span className="text-caption font-caption">
              {t("autonomous.topicDriven.backToResults")}
            </span>
          </LinkButton>
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-subtext-color">ID: {section.id.slice(0, 16)}...</span>
            {statusBadge()}
            {isPolling && (
              <div className="flex items-center gap-1 rounded-full bg-success-50 px-2 py-0.5">
                <FeatherRefreshCw className="h-3 w-3 text-success-600" />
                <span className="text-[11px] text-success-600">
                  {t("autonomous.topicDriven.autoUpdating")}
                </span>
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <FeatherFlaskConical className="text-body font-body text-brand-600" />
          {isEditingTitle ? (
            <div className="flex items-center gap-2">
              <TextField className="h-auto" variant="outline" label="" helpText="">
                <TextField.Input
                  value={titleDraft}
                  onChange={(e) => setTitleDraft(e.target.value)}
                />
              </TextField>
              <Button
                variant="brand-primary"
                size="small"
                disabled={isUpdatingTitle}
                onClick={handleSaveTitle}
              >
                {isUpdatingTitle
                  ? t("autonomous.topicDriven.saving")
                  : t("autonomous.topicDriven.save")}
              </Button>
              <Button
                variant="neutral-secondary"
                size="small"
                onClick={() => {
                  setIsEditingTitle(false);
                  setTitleDraft(section.title);
                }}
              >
                {t("autonomous.topicDriven.cancel")}
              </Button>
            </div>
          ) : (
            <>
              <span className="text-body-bold font-body-bold text-default-font">
                {section.title}
              </span>
              <IconButton
                variant="neutral-tertiary"
                size="small"
                icon={<FeatherEdit2 />}
                onClick={() => setIsEditingTitle(true)}
              />
            </>
          )}
        </div>
      </div>

      <div className="flex w-full grow shrink-0 basis-0 flex-col items-center px-6 py-6 overflow-auto">
        <div className="flex w-full max-w-[768px] flex-col items-start gap-4">
          {error && (
            <div className="flex w-full items-center rounded-md bg-error-50 px-4 py-3">
              <span className="text-body font-body text-error-600">{error}</span>
            </div>
          )}

          {status?.research_history && (
            <div className="flex w-full flex-col items-start gap-2 rounded-lg border border-solid border-neutral-border bg-default-background px-4 py-3 shadow-sm">
              <span className="text-body-bold font-body-bold text-default-font">
                {t("autonomous.topicDriven.researchHistory")}
              </span>
              <span className="text-body font-body text-subtext-color">
                {t("autonomous.topicDriven.purpose")}:{" "}
                {status.research_history.research_topic ?? "N/A"}
              </span>
              {status.research_history.paper_url && (
                <span className="text-body font-body text-subtext-color">
                  {t("autonomous.topicDriven.paperUrl")}: {status.research_history.paper_url}
                </span>
              )}
            </div>
          )}

          {!snapshot.research_topic &&
            !snapshot.queries?.length &&
            !snapshot.paper_titles?.length &&
            !snapshot.research_hypothesis &&
            !snapshot.experimental_design &&
            !snapshot.github_url &&
            !snapshot.experimental_results &&
            !snapshot.experimental_analysis &&
            !snapshot.paper_content && (
              <div className="flex w-full flex-col items-center gap-4 py-12">
                <span className="text-body font-body text-subtext-color">
                  {t("autonomous.topicDriven.noProgress")}
                </span>
              </div>
            )}

          {snapshot.research_topic && (
            <ResultSection
              title="research_topic"
              icon={<FeatherFileText className="text-body font-body text-brand-500" />}
            >
              <span className="text-body font-body text-default-font whitespace-pre-wrap">
                {snapshot.research_topic}
              </span>
            </ResultSection>
          )}

          {snapshot.queries && snapshot.queries.length > 0 && (
            <ResultSection
              title="queries"
              icon={<FeatherSearch className="text-body font-body text-success-500" />}
              badge={<Badge variant="neutral">{snapshot.queries.length}件</Badge>}
            >
              {snapshot.queries.map((q) => (
                <div key={q} className="flex items-start gap-2">
                  <span className="text-body font-body text-subtext-color">•</span>
                  <span className="text-body font-body text-default-font">{q}</span>
                </div>
              ))}
            </ResultSection>
          )}

          {snapshot.paper_titles && snapshot.paper_titles.length > 0 && (
            <ResultSection
              title="paper_titles"
              icon={<FeatherBookOpen className="text-body font-body text-warning-500" />}
              badge={<Badge variant="neutral">{snapshot.paper_titles.length}件</Badge>}
            >
              {snapshot.paper_titles.map((t) => (
                <div key={t} className="flex items-start gap-2">
                  <span className="text-body font-body text-subtext-color">•</span>
                  <span className="text-body font-body text-default-font">{t}</span>
                </div>
              ))}
            </ResultSection>
          )}

          {snapshot.research_hypothesis && (
            <ToggleResultSection
              title="research_hypothesis"
              icon={<FeatherLightbulb className="text-body font-body text-error-500" />}
              isOpen={openSections.researchHypothesis}
              onToggle={() => toggleSection("researchHypothesis")}
            >
              <FieldBlock
                label="open_problems"
                value={snapshot.research_hypothesis.open_problems}
              />
              <FieldBlock label="method" value={snapshot.research_hypothesis.method} />
              <FieldBlock
                label="primary_metric"
                value={snapshot.research_hypothesis.primary_metric}
              />
              <FieldBlock
                label="expected_result"
                value={snapshot.research_hypothesis.expected_result}
              />
              <FieldBlock
                label="experimental_setup"
                value={snapshot.research_hypothesis.experimental_setup}
              />
              <FieldBlock
                label="expected_conclusion"
                value={snapshot.research_hypothesis.expected_conclusion}
              />
            </ToggleResultSection>
          )}

          {snapshot.experimental_design && (
            <ToggleResultSection
              title="experimental_design"
              icon={<FeatherClipboard className="text-body font-body text-brand-500" />}
              isOpen={openSections.experimentalDesign}
              onToggle={() => toggleSection("experimentalDesign")}
            >
              <FieldBlock
                label="experiment_summary"
                value={snapshot.experimental_design.experiment_summary}
              />
              {snapshot.experimental_design.evaluation_metrics &&
                snapshot.experimental_design.evaluation_metrics.length > 0 && (
                  <div className="flex w-full flex-col items-start gap-2">
                    <span className="text-caption-bold font-caption-bold text-subtext-color">
                      evaluation_metrics
                    </span>
                    <div className="flex w-full flex-wrap items-start gap-2">
                      {snapshot.experimental_design.evaluation_metrics.map((metric) => (
                        <div
                          key={metric.name || metric.description}
                          className="flex flex-col items-start gap-1 rounded-md bg-neutral-50 px-3 py-2"
                        >
                          <span className="text-body-bold font-body-bold text-default-font">
                            {metric.name}
                          </span>
                          {metric.description && (
                            <span className="text-caption font-caption text-subtext-color">
                              {metric.description}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              {snapshot.experimental_design.models_to_use && (
                <div className="flex w-full flex-col items-start gap-1">
                  <span className="text-caption-bold font-caption-bold text-subtext-color">
                    models_to_use
                  </span>
                  <div className="flex flex-wrap items-center gap-2">
                    {snapshot.experimental_design.models_to_use.map((m) => (
                      <Badge key={m} variant="neutral">
                        {m}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {snapshot.experimental_design.datasets_to_use && (
                <div className="flex w-full flex-col items-start gap-1">
                  <span className="text-caption-bold font-caption-bold text-subtext-color">
                    datasets_to_use
                  </span>
                  <div className="flex flex-wrap items-center gap-2">
                    {snapshot.experimental_design.datasets_to_use.map((d) => (
                      <Badge key={d} variant="neutral">
                        {d}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {snapshot.experimental_design.proposed_method && (
                <div className="flex w-full flex-col items-start gap-1">
                  <span className="text-caption-bold font-caption-bold text-subtext-color">
                    proposed_method
                  </span>
                  <span className="text-body font-body text-default-font">
                    {snapshot.experimental_design.proposed_method.method_name}:{" "}
                    {snapshot.experimental_design.proposed_method.description}
                  </span>
                </div>
              )}
              {snapshot.experimental_design.comparative_methods &&
                snapshot.experimental_design.comparative_methods.length > 0 && (
                  <div className="flex w-full flex-col items-start gap-2">
                    <span className="text-caption-bold font-caption-bold text-subtext-color">
                      comparative_methods
                    </span>
                    <div className="flex w-full flex-wrap items-start gap-2">
                      {snapshot.experimental_design.comparative_methods.map((method) => (
                        <div
                          key={method.method_name || method.description}
                          className="flex flex-col items-start gap-1 rounded-md border border-solid border-neutral-border bg-default-background px-3 py-2"
                        >
                          <span className="text-body-bold font-body-bold text-default-font">
                            {method.method_name}
                          </span>
                          {method.description && (
                            <span className="text-caption font-caption text-subtext-color">
                              {method.description}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
            </ToggleResultSection>
          )}

          {snapshot.github_url && (
            <ResultSection
              title="github_url"
              icon={<FeatherGithub className="text-body font-body text-neutral-500" />}
            >
              <a
                href={snapshot.github_url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 text-brand-600 hover:underline"
              >
                <FeatherExternalLink className="text-body font-body" />
                <span className="text-body font-body break-all">{snapshot.github_url}</span>
              </a>
            </ResultSection>
          )}

          {snapshot.experimental_results && (
            <ToggleResultSection
              title="experimental_results"
              icon={<FeatherTerminal className="text-body font-body text-success-500" />}
              isOpen={openSections.experimentalResults}
              onToggle={() => toggleSection("experimentalResults")}
            >
              {snapshot.experimental_results.stdout && (
                <div className="flex w-full flex-col items-start gap-2">
                  <span className="text-caption-bold font-caption-bold text-subtext-color">
                    stdout
                  </span>
                  <div className="flex w-full flex-col items-start rounded-md bg-neutral-100 px-3 py-2">
                    <span className="text-monospace-body font-monospace-body text-default-font whitespace-pre-wrap">
                      {snapshot.experimental_results.stdout}
                    </span>
                  </div>
                </div>
              )}
              {snapshot.experimental_results.stderr && (
                <div className="flex w-full flex-col items-start gap-2">
                  <span className="text-caption-bold font-caption-bold text-subtext-color">
                    stderr
                  </span>
                  <div className="flex w-full flex-col items-start rounded-md bg-neutral-100 px-3 py-2">
                    <span className="text-monospace-body font-monospace-body text-subtext-color whitespace-pre-wrap">
                      {snapshot.experimental_results.stderr}
                    </span>
                  </div>
                </div>
              )}
              {snapshot.experimental_results.metrics_data &&
                Object.keys(snapshot.experimental_results.metrics_data).length > 0 && (
                  <div className="flex w-full flex-col items-start gap-2">
                    <span className="text-caption-bold font-caption-bold text-subtext-color">
                      metrics_data
                    </span>
                    <div className="flex w-full flex-col items-start rounded-md bg-neutral-100 px-3 py-2">
                      <pre className="text-monospace-body font-monospace-body text-default-font whitespace-pre-wrap max-h-80 overflow-auto w-full">
                        {JSON.stringify(snapshot.experimental_results.metrics_data, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
            </ToggleResultSection>
          )}

          {snapshot.experimental_analysis && (
            <ResultSection
              title="experimental_analysis"
              icon={<FeatherBarChart3 className="text-body font-body text-warning-500" />}
            >
              <span className="text-body font-body text-default-font whitespace-pre-wrap">
                {snapshot.experimental_analysis.analysis_report}
              </span>
            </ResultSection>
          )}

          {snapshot.paper_content && (
            <ToggleResultSection
              title="paper_content"
              icon={<FeatherFileText className="text-body font-body text-error-500" />}
              isOpen={openSections.paperContent}
              onToggle={() => toggleSection("paperContent")}
            >
              <FieldBlock label="title" value={snapshot.paper_content.title} bold />
              <FieldBlock label="abstract" value={snapshot.paper_content.abstract} />
              <FieldBlock label="introduction" value={snapshot.paper_content.introduction} />
              <FieldBlock label="related_work" value={snapshot.paper_content.related_work} />
              <FieldBlock label="background" value={snapshot.paper_content.background} />
              <FieldBlock label="method" value={snapshot.paper_content.method} />
              <FieldBlock
                label="experimental_setup"
                value={snapshot.paper_content.experimental_setup}
              />
              <FieldBlock label="results" value={snapshot.paper_content.results} />
              <FieldBlock label="conclusion" value={snapshot.paper_content.conclusion} />
            </ToggleResultSection>
          )}
        </div>
      </div>
    </div>
  );
}

function ResultSection({
  title,
  icon,
  badge,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  badge?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="flex w-full flex-col items-start gap-4 rounded-lg border border-solid border-neutral-border bg-default-background shadow-sm">
      <div className="flex w-full items-center gap-2 border-b border-solid border-neutral-border px-4 py-3">
        {icon}
        <span className="text-body-bold font-body-bold text-default-font">{title}</span>
        {badge}
      </div>
      <div className="flex w-full flex-col items-start gap-2 px-4 pb-4">{children}</div>
    </div>
  );
}

function ToggleResultSection({
  title,
  icon,
  isOpen,
  onToggle,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="flex w-full flex-col items-start rounded-lg border border-solid border-neutral-border bg-default-background shadow-sm">
      <button
        type="button"
        className="flex w-full items-center justify-between border-b border-solid border-neutral-border px-4 py-3 cursor-pointer"
        onClick={onToggle}
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-body-bold font-body-bold text-default-font">{title}</span>
        </div>
        {isOpen ? (
          <FeatherChevronUp className="text-body font-body text-subtext-color" />
        ) : (
          <FeatherChevronDown className="text-body font-body text-subtext-color" />
        )}
      </button>
      {isOpen && <div className="flex w-full flex-col items-start gap-4 px-4 py-4">{children}</div>}
    </div>
  );
}

function FieldBlock({
  label,
  value,
  bold,
}: {
  label: string;
  value?: string | null;
  bold?: boolean;
}) {
  if (!value) return null;
  return (
    <div className="flex w-full flex-col items-start gap-1">
      <span className="text-caption-bold font-caption-bold text-subtext-color">{label}</span>
      <span
        className={`text-body font-body text-default-font whitespace-pre-wrap ${bold ? "text-body-bold font-body-bold" : ""}`}
      >
        {value}
      </span>
    </div>
  );
}
