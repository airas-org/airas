"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { EphemeralCloudRunnerConfig, StaticRunnerConfig } from "@/lib/api";

const RequiredMark = () => <span className="text-rose-400 ml-0.5">*</span>;

export type RunnerConfigFormState =
  | { type: "static"; runnerLabels: string }
  | {
      type: "ephemeral_cloud";
      cloudProvider: "aws" | "gcp";
      gpuInstanceType: string;
      maxInstanceHours: string;
    };

export const defaultRunnerConfigFormState: RunnerConfigFormState = {
  type: "static",
  runnerLabels: "ubuntu-latest",
};

export function isRunnerConfigFormValid(state: RunnerConfigFormState): boolean {
  if (state.type === "static") {
    return state.runnerLabels.trim().length > 0;
  }
  return true;
}

export function toRunnerConfigPayload(
  state: RunnerConfigFormState,
): StaticRunnerConfig | EphemeralCloudRunnerConfig {
  if (state.type === "static") {
    return {
      type: "static",
      runner_label: state.runnerLabels
        .split(",")
        .map((l) => l.trim())
        .filter((l) => l.length > 0),
    };
  }
  return {
    type: "ephemeral_cloud",
    cloud_provider: state.cloudProvider as EphemeralCloudRunnerConfig.cloud_provider,
    gpu_instance_type: state.gpuInstanceType || undefined,
    max_instance_hours: state.maxInstanceHours || undefined,
  };
}

interface RunnerConfigFormProps {
  idPrefix: string;
  value: RunnerConfigFormState;
  onChange: (value: RunnerConfigFormState) => void;
}

export function RunnerConfigForm({ idPrefix, value, onChange }: RunnerConfigFormProps) {
  const handleTypeChange = (type: "static" | "ephemeral_cloud") => {
    if (type === "static") {
      onChange({ type: "static", runnerLabels: "ubuntu-latest" });
    } else {
      onChange({
        type: "ephemeral_cloud",
        cloudProvider: "aws",
        gpuInstanceType: "g4dn.xlarge",
        maxInstanceHours: "120",
      });
    }
  };

  return (
    <div className="space-y-3 rounded-md bg-muted/40 p-4">
      <p className="text-sm font-semibold text-foreground">GitHub Actions Runners</p>
      <div className="space-y-2">
        <Label htmlFor={`${idPrefix}-runner-type`}>タイプ</Label>
        <Select
          value={value.type}
          onValueChange={(val) => handleTypeChange(val as "static" | "ephemeral_cloud")}
        >
          <SelectTrigger id={`${idPrefix}-runner-type`} className="w-full md:w-72">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="static">セルフホスト / GitHub ホスト</SelectItem>
            <SelectItem value="ephemeral_cloud">クラウド（オンデマンド）</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {value.type === "static" && (
        <div className="space-y-2 mt-1">
          <Label htmlFor={`${idPrefix}-runner-labels`}>
            ラベル
            <RequiredMark />
          </Label>
          <Input
            id={`${idPrefix}-runner-labels`}
            value={value.runnerLabels}
            onChange={(e) => onChange({ ...value, runnerLabels: e.target.value })}
            placeholder="ubuntu-latest,gpu-runner"
          />
        </div>
      )}

      {value.type === "ephemeral_cloud" && (
        <div className="grid gap-4 md:grid-cols-3 mt-2">
          <div className="space-y-2">
            <Label htmlFor={`${idPrefix}-cloud-provider`}>クラウドプロバイダー</Label>
            <Select
              value={value.cloudProvider}
              onValueChange={(val) => onChange({ ...value, cloudProvider: val as "aws" | "gcp" })}
            >
              <SelectTrigger id={`${idPrefix}-cloud-provider`} className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="aws">AWS</SelectItem>
                <SelectItem value="gcp">GCP</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor={`${idPrefix}-gpu-instance-type`}>インスタンスタイプ</Label>
            <Input
              id={`${idPrefix}-gpu-instance-type`}
              value={value.gpuInstanceType}
              onChange={(e) => onChange({ ...value, gpuInstanceType: e.target.value })}
              placeholder="g4dn.xlarge"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor={`${idPrefix}-max-instance-hours`}>最大稼働時間 (h)</Label>
            <Input
              id={`${idPrefix}-max-instance-hours`}
              type="number"
              inputMode="numeric"
              value={value.maxInstanceHours}
              onChange={(e) => onChange({ ...value, maxInstanceHours: e.target.value })}
              placeholder="120"
            />
          </div>
        </div>
      )}
    </div>
  );
}
