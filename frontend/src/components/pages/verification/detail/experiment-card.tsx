import { FeatherChevronDown, FeatherChevronRight } from "@subframe/core";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { MathMarkdown } from "@/components/shared/math-markdown";
import { Loader, Table } from "@/ui";
import type { ExperimentSetting } from "../types";

interface ExperimentCardProps {
  experiment: ExperimentSetting;
  onRun: (id: string) => void;
}

export function ExperimentCard({ experiment, onRun }: ExperimentCardProps) {
  const { t } = useTranslation();
  const [resultExpanded, setResultExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h3 className="text-sm font-semibold text-foreground">{experiment.title}</h3>
      <MathMarkdown className="text-xs text-muted-foreground mt-1 [&>p]:m-0">
        {experiment.description}
      </MathMarkdown>
      <div className="mt-2 space-y-1">
        {experiment.parameters.map((param) => (
          <div key={param.name} className="text-xs">
            <span className="text-muted-foreground">{param.name}:</span>{" "}
            <span className="text-foreground">{param.value}</span>
          </div>
        ))}
      </div>
      <div className="mt-3">
        {experiment.status === "pending" && (
          <button
            type="button"
            onClick={() => onRun(experiment.id)}
            className="rounded-md bg-neutral-200 px-3 py-1.5 text-xs font-medium text-neutral-700 hover:bg-neutral-300 hover:text-neutral-900 transition-colors cursor-pointer"
          >
            Run experiment
          </button>
        )}
        {experiment.status === "running" && (
          <div className="flex items-center gap-2">
            <Loader size="small" />
            <span className="text-xs text-muted-foreground">Running...</span>
          </div>
        )}
        {experiment.status === "completed" && experiment.result && (
          <div>
            <button
              type="button"
              onClick={() => setResultExpanded((prev) => !prev)}
              className="flex items-center gap-1.5 text-xs font-medium text-subtext-color hover:text-default-font transition-colors cursor-pointer"
            >
              {resultExpanded ? (
                <FeatherChevronDown className="h-3.5 w-3.5" />
              ) : (
                <FeatherChevronRight className="h-3.5 w-3.5" />
              )}
              {t("verification.detail.experimentSettings.experimentResults")}
            </button>
            {resultExpanded && (
              <div className="mt-2 space-y-3">
                <MathMarkdown className="text-xs text-muted-foreground [&>p]:m-0">
                  {experiment.result.summary}
                </MathMarkdown>
                <Table
                  header={
                    <Table.HeaderRow>
                      <Table.HeaderCell>Metric</Table.HeaderCell>
                      <Table.HeaderCell>Value</Table.HeaderCell>
                    </Table.HeaderRow>
                  }
                >
                  {Object.entries(experiment.result.metrics).map(([key, value]) => (
                    <Table.Row key={key}>
                      <Table.Cell>{key}</Table.Cell>
                      <Table.Cell>{value}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table>
                <MathMarkdown className="text-xs text-muted-foreground [&>p]:m-0">
                  {experiment.result.details}
                </MathMarkdown>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
