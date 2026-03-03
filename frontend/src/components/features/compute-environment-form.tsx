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
import { Textarea } from "@/components/ui/textarea";
import type { ComputeEnvironment } from "@/lib/api";

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

const toNumber = (value: string): number | undefined => {
  if (value.trim() === "") return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
};

export function toComputeEnvironmentPayload(
  state: ComputeEnvironmentFormState,
): ComputeEnvironment {
  return {
    os: state.os || undefined,
    cpu_cores: toNumber(state.cpuCores),
    ram_gb: toNumber(state.ramGb),
    gpu_type: state.gpuType || undefined,
    gpu_count: toNumber(state.gpuCount),
    gpu_memory_gb: toNumber(state.gpuMemoryGb),
    cuda_version: state.cudaVersion || undefined,
    python_version: state.pythonVersion || undefined,
    storage_type: (state.storageType as "nvme" | "ssd" | "hdd") || undefined,
    storage_gb: toNumber(state.storageGb),
    description: state.description || undefined,
  };
}

interface ComputeEnvironmentFormProps {
  idPrefix: string;
  value: ComputeEnvironmentFormState;
  onChange: (value: ComputeEnvironmentFormState) => void;
}

export function ComputeEnvironmentForm({ idPrefix, value, onChange }: ComputeEnvironmentFormProps) {
  const set =
    <K extends keyof ComputeEnvironmentFormState>(key: K) =>
    (next: ComputeEnvironmentFormState[K]) =>
      onChange({ ...value, [key]: next });

  return (
    <div className="space-y-3 rounded-md bg-muted/40 p-4">
      <p className="text-sm font-semibold text-foreground">計算環境</p>
      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-os`}>OS</Label>
          <Input
            id={`${idPrefix}-os`}
            value={value.os}
            onChange={(e) => set("os")(e.target.value)}
            placeholder="Ubuntu 22.04"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-cpu-cores`}>CPU コア数</Label>
          <Input
            id={`${idPrefix}-cpu-cores`}
            type="number"
            inputMode="numeric"
            value={value.cpuCores}
            onChange={(e) => set("cpuCores")(e.target.value)}
            placeholder="8"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-ram`}>RAM (GB)</Label>
          <Input
            id={`${idPrefix}-ram`}
            type="number"
            inputMode="numeric"
            value={value.ramGb}
            onChange={(e) => set("ramGb")(e.target.value)}
            placeholder="64"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-gpu-type`}>GPU 種類</Label>
          <Input
            id={`${idPrefix}-gpu-type`}
            value={value.gpuType}
            onChange={(e) => set("gpuType")(e.target.value)}
            placeholder="NVIDIA A100"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-gpu-count`}>GPU 数</Label>
          <Input
            id={`${idPrefix}-gpu-count`}
            type="number"
            inputMode="numeric"
            value={value.gpuCount}
            onChange={(e) => set("gpuCount")(e.target.value)}
            placeholder="1"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-gpu-memory`}>GPU VRAM (GB)</Label>
          <Input
            id={`${idPrefix}-gpu-memory`}
            type="number"
            inputMode="numeric"
            value={value.gpuMemoryGb}
            onChange={(e) => set("gpuMemoryGb")(e.target.value)}
            placeholder="40"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-cuda-version`}>CUDA バージョン</Label>
          <Input
            id={`${idPrefix}-cuda-version`}
            value={value.cudaVersion}
            onChange={(e) => set("cudaVersion")(e.target.value)}
            placeholder="12.1"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-python-version`}>Python バージョン</Label>
          <Input
            id={`${idPrefix}-python-version`}
            value={value.pythonVersion}
            onChange={(e) => set("pythonVersion")(e.target.value)}
            placeholder="3.11"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-storage-type`}>ストレージ種類</Label>
          <Select
            value={value.storageType}
            onValueChange={(val) => set("storageType")(val as "nvme" | "ssd" | "hdd" | "")}
          >
            <SelectTrigger id={`${idPrefix}-storage-type`} className="w-full">
              <SelectValue placeholder="選択..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="nvme">NVMe</SelectItem>
              <SelectItem value="ssd">SSD</SelectItem>
              <SelectItem value="hdd">HDD</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-storage-gb`}>ストレージ容量 (GB)</Label>
          <Input
            id={`${idPrefix}-storage-gb`}
            type="number"
            inputMode="numeric"
            value={value.storageGb}
            onChange={(e) => set("storageGb")(e.target.value)}
            placeholder="500"
          />
        </div>
      </div>
      <div className="space-y-2">
        <Label htmlFor={`${idPrefix}-compute-env-desc`}>補足情報</Label>
        <Textarea
          id={`${idPrefix}-compute-env-desc`}
          value={value.description}
          onChange={(e) => set("description")(e.target.value)}
          placeholder="上記フィールドに収まらない環境情報（ネットワーク帯域、特殊な依存関係など）"
        />
      </div>
    </div>
  );
}
