import type { EphemeralCloudRunnerConfig } from "@/lib/api";
import { Select } from "@/ui/components/Select";
import { TextField } from "@/ui/components/TextField";

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
    return state.runnerLabels.split(",").some((l) => l.trim().length > 0);
  }
  const hours = Number(state.maxInstanceHours);
  return Number.isInteger(hours) && hours >= 1;
}

export function toRunnerConfigPayload(state: RunnerConfigFormState) {
  if (state.type === "static") {
    return {
      type: "static" as const,
      runner_label: state.runnerLabels
        .split(",")
        .map((l) => l.trim())
        .filter((l) => l.length > 0),
    };
  }
  return {
    type: "ephemeral_cloud" as const,
    cloud_provider: state.cloudProvider as EphemeralCloudRunnerConfig.cloud_provider,
    gpu_instance_type: state.gpuInstanceType || undefined,
    max_instance_hours: state.maxInstanceHours ? Number(state.maxInstanceHours) : undefined,
  };
}

export interface RunnerConfigFormLabels {
  runnerType: string;
  runnerTypeStatic: string;
  runnerTypeCloud: string;
  runnerLabel: string;
  cloudProvider: string;
  gpuInstanceType: string;
  maxInstanceHours: string;
}

interface RunnerConfigFormProps {
  value: RunnerConfigFormState;
  onChange: (value: RunnerConfigFormState) => void;
  labels: RunnerConfigFormLabels;
}

export function RunnerConfigForm({ value, onChange, labels }: RunnerConfigFormProps) {
  const handleTypeChange = (type: string) => {
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
    <div className="flex w-full flex-col items-start gap-3">
      <Select
        className="h-auto w-full flex-none"
        variant="outline"
        label={labels.runnerType}
        helpText=""
        value={value.type}
        onValueChange={handleTypeChange}
      >
        <Select.Item value="static">{labels.runnerTypeStatic}</Select.Item>
        <Select.Item value="ephemeral_cloud">{labels.runnerTypeCloud}</Select.Item>
      </Select>
      {value.type === "static" && (
        <div className="flex w-full flex-col items-start gap-1">
          <div className="flex items-center gap-1">
            <span className="text-caption font-caption text-default-font">
              {labels.runnerLabel}
            </span>
            <span className="text-caption font-caption text-error-500">*</span>
          </div>
          <TextField className="h-auto w-full flex-none" variant="outline" label="" helpText="">
            <TextField.Input
              placeholder="ubuntu-latest, gpu-runner"
              value={value.runnerLabels}
              onChange={(e) => onChange({ ...value, runnerLabels: e.target.value })}
            />
          </TextField>
        </div>
      )}
      {value.type === "ephemeral_cloud" && (
        <div className="flex w-full flex-wrap items-start gap-3">
          <Select
            className="h-auto min-w-[120px] grow shrink-0 basis-0"
            variant="outline"
            label={labels.cloudProvider}
            helpText=""
            value={value.cloudProvider}
            onValueChange={(val) => onChange({ ...value, cloudProvider: val as "aws" | "gcp" })}
          >
            <Select.Item value="aws">AWS</Select.Item>
            <Select.Item value="gcp">GCP</Select.Item>
          </Select>
          <TextField
            className="h-auto min-w-[120px] grow shrink-0 basis-0"
            variant="outline"
            label={labels.gpuInstanceType}
            helpText=""
          >
            <TextField.Input
              placeholder="g4dn.xlarge"
              value={value.gpuInstanceType}
              onChange={(e) => onChange({ ...value, gpuInstanceType: e.target.value })}
            />
          </TextField>
          <TextField
            className="h-auto min-w-[120px] grow shrink-0 basis-0"
            variant="outline"
            label={labels.maxInstanceHours}
            helpText=""
          >
            <TextField.Input
              type="number"
              placeholder="120"
              value={value.maxInstanceHours}
              onChange={(e) => onChange({ ...value, maxInstanceHours: e.target.value })}
            />
          </TextField>
        </div>
      )}
    </div>
  );
}
