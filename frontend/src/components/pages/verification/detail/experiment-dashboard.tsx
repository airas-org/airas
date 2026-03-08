import { useTranslation } from "react-i18next";
import { BarChart } from "@/ui";
import type { ExperimentSetting } from "../types";

interface ExperimentDashboardProps {
  experiments: ExperimentSetting[];
}

export function ExperimentDashboard({ experiments }: ExperimentDashboardProps) {
  const { t } = useTranslation();
  const completedExperiments = experiments.filter(
    (exp): exp is ExperimentSetting & { result: NonNullable<ExperimentSetting["result"]> } =>
      exp.status === "completed" && exp.result != null,
  );

  if (completedExperiments.length < 2) return null;

  const metricKeys = Object.keys(completedExperiments[0].result.metrics);

  const chartData = completedExperiments.map((exp) => ({
    name: exp.title.length > 20 ? `${exp.title.slice(0, 20)}...` : exp.title,
    ...exp.result.metrics,
  }));

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <h2 className="text-lg font-semibold text-foreground">
        {t("verification.detail.experimentDashboard.title")}
      </h2>
      <p className="text-sm text-muted-foreground mt-1">
        {t("verification.detail.experimentDashboard.subtitle", {
          count: completedExperiments.length,
        })}
      </p>
      <div className="mt-4">
        <BarChart data={chartData} categories={metricKeys} index="name" />
      </div>
    </div>
  );
}
