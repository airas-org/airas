import type { ComputeEnvironment } from "@/lib/api";
import { Select } from "@/ui/components/Select";
import { TextArea } from "@/ui/components/TextArea";
import { TextField } from "@/ui/components/TextField";

export type ComputeEnvironmentFormState = {
  os: string;
  cpuCores: string;
  ramGb: string;
  gpuType: string;
  gpuCount: string;
  gpuMemoryGb: string;
  cudaVersion: string;
  pythonVersion: string;
  storageType: "nvme" | "ssd" | "hdd" | "";
  storageGb: string;
  description: string;
};

export const defaultComputeEnvironmentFormState: ComputeEnvironmentFormState = {
  os: "",
  cpuCores: "",
  ramGb: "",
  gpuType: "",
  gpuCount: "",
  gpuMemoryGb: "",
  cudaVersion: "",
  pythonVersion: "",
  storageType: "",
  storageGb: "",
  description: "",
};

const toInteger = (value: string): number | undefined => {
  if (value.trim() === "") return undefined;
  const parsed = Number(value);
  return Number.isInteger(parsed) ? parsed : undefined;
};

export function toComputeEnvironmentPayload(
  state: ComputeEnvironmentFormState,
): ComputeEnvironment {
  return {
    os: state.os || undefined,
    cpu_cores: toInteger(state.cpuCores),
    ram_gb: toInteger(state.ramGb),
    gpu_type: state.gpuType || undefined,
    gpu_count: toInteger(state.gpuCount),
    gpu_memory_gb: toInteger(state.gpuMemoryGb),
    cuda_version: state.cudaVersion || undefined,
    python_version: state.pythonVersion || undefined,
    storage_type: (state.storageType as "nvme" | "ssd" | "hdd") || undefined,
    storage_gb: toInteger(state.storageGb),
    description: state.description || undefined,
  };
}

export interface ComputeEnvironmentFormLabels {
  cpuCores: string;
  gpuType: string;
  gpuCount: string;
  storageType: string;
  storageGb: string;
  description: string;
  descriptionPlaceholder: string;
}

interface ComputeEnvironmentFormProps {
  value: ComputeEnvironmentFormState;
  onChange: (value: ComputeEnvironmentFormState) => void;
  labels: ComputeEnvironmentFormLabels;
}

export function ComputeEnvironmentForm({ value, onChange, labels }: ComputeEnvironmentFormProps) {
  const set =
    <K extends keyof ComputeEnvironmentFormState>(key: K) =>
    (next: ComputeEnvironmentFormState[K]) =>
      onChange({ ...value, [key]: next });

  return (
    <div className="flex w-full flex-col items-start gap-3">
      <div className="flex w-full flex-wrap items-start gap-3">
        <TextField
          className="h-auto min-w-[120px] grow shrink-0 basis-0"
          variant="outline"
          label="OS"
          helpText=""
        >
          <TextField.Input
            placeholder="Ubuntu 22.04"
            value={value.os}
            onChange={(e) => set("os")(e.target.value)}
          />
        </TextField>
        <TextField
          className="h-auto min-w-[120px] grow shrink-0 basis-0"
          variant="outline"
          label={labels.cpuCores}
          helpText=""
        >
          <TextField.Input
            type="number"
            placeholder="8"
            value={value.cpuCores}
            onChange={(e) => set("cpuCores")(e.target.value)}
          />
        </TextField>
        <TextField
          className="h-auto min-w-[120px] grow shrink-0 basis-0"
          variant="outline"
          label="RAM (GB)"
          helpText=""
        >
          <TextField.Input
            type="number"
            placeholder="64"
            value={value.ramGb}
            onChange={(e) => set("ramGb")(e.target.value)}
          />
        </TextField>
      </div>
      <div className="flex w-full flex-wrap items-start gap-3">
        <TextField
          className="h-auto min-w-[120px] grow shrink-0 basis-0"
          variant="outline"
          label={labels.gpuType}
          helpText=""
        >
          <TextField.Input
            placeholder="NVIDIA A100"
            value={value.gpuType}
            onChange={(e) => set("gpuType")(e.target.value)}
          />
        </TextField>
        <TextField
          className="h-auto min-w-[120px] grow shrink-0 basis-0"
          variant="outline"
          label={labels.gpuCount}
          helpText=""
        >
          <TextField.Input
            type="number"
            placeholder="1"
            value={value.gpuCount}
            onChange={(e) => set("gpuCount")(e.target.value)}
          />
        </TextField>
        <TextField
          className="h-auto min-w-[120px] grow shrink-0 basis-0"
          variant="outline"
          label="GPU VRAM (GB)"
          helpText=""
        >
          <TextField.Input
            type="number"
            placeholder="40"
            value={value.gpuMemoryGb}
            onChange={(e) => set("gpuMemoryGb")(e.target.value)}
          />
        </TextField>
      </div>
      <div className="flex w-full flex-wrap items-start gap-3">
        <TextField
          className="h-auto min-w-[120px] grow shrink-0 basis-0"
          variant="outline"
          label="CUDA"
          helpText=""
        >
          <TextField.Input
            placeholder="12.1"
            value={value.cudaVersion}
            onChange={(e) => set("cudaVersion")(e.target.value)}
          />
        </TextField>
        <TextField
          className="h-auto min-w-[120px] grow shrink-0 basis-0"
          variant="outline"
          label="Python"
          helpText=""
        >
          <TextField.Input
            placeholder="3.11"
            value={value.pythonVersion}
            onChange={(e) => set("pythonVersion")(e.target.value)}
          />
        </TextField>
        <Select
          className="h-auto min-w-[120px] grow shrink-0 basis-0"
          variant="outline"
          label={labels.storageType}
          placeholder="--"
          helpText=""
          value={value.storageType}
          onValueChange={(val) => set("storageType")(val as "nvme" | "ssd" | "hdd" | "")}
        >
          <Select.Item value="nvme">NVMe</Select.Item>
          <Select.Item value="ssd">SSD</Select.Item>
          <Select.Item value="hdd">HDD</Select.Item>
        </Select>
        <TextField
          className="h-auto min-w-[120px] grow shrink-0 basis-0"
          variant="outline"
          label={labels.storageGb}
          helpText=""
        >
          <TextField.Input
            type="number"
            placeholder="500"
            value={value.storageGb}
            onChange={(e) => set("storageGb")(e.target.value)}
          />
        </TextField>
      </div>
      <TextArea
        className="h-auto w-full flex-none"
        variant="outline"
        label={labels.description}
        helpText=""
      >
        <TextArea.Input
          placeholder={labels.descriptionPlaceholder}
          value={value.description}
          onChange={(e) => set("description")(e.target.value)}
        />
      </TextArea>
    </div>
  );
}
