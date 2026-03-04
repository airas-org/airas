import { FeatherChevronDown, FeatherChevronRight, FeatherPlus } from "@subframe/core";
import { useState } from "react";
import { Table } from "@/ui";
import type { ImplementationInfo } from "../types";
import { ExperimentCard } from "./experiment-card";

interface ImplementationResultProps {
  implementation: ImplementationInfo;
  onRunExperiment: (id: string) => void;
}

export function ImplementationResult({
  implementation,
  onRunExperiment,
}: ImplementationResultProps) {
  const [othersExpanded, setOthersExpanded] = useState(false);

  const mainParams = implementation.fixedParameters.slice(0, 2);
  const otherParams = implementation.fixedParameters.slice(2);

  return (
    <>
      <div id="sec-code" className="rounded-lg border border-border bg-card p-6">
        <h2 className="text-lg font-semibold text-foreground">実験コード</h2>
        <div className="mt-3 flex items-center gap-2">
          <span className="text-sm font-medium text-foreground">GitHub URL:</span>
          <a
            href={implementation.githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-brand-600 hover:underline"
          >
            {implementation.githubUrl}
          </a>
        </div>
      </div>

      <div id="sec-settings" className="rounded-lg border border-border bg-card p-6">
        <h2 className="text-lg font-semibold text-foreground">実験設定</h2>

        <div className="mt-4">
          <p className="text-xs font-medium text-foreground">主要パラメータ</p>
          <div className="mt-1.5 rounded-md border border-solid border-neutral-border overflow-hidden">
            <Table
              header={
                <Table.HeaderRow>
                  <Table.HeaderCell className="text-[11px]">名称</Table.HeaderCell>
                  <Table.HeaderCell className="text-[11px]">説明</Table.HeaderCell>
                </Table.HeaderRow>
              }
            >
              {mainParams.map((param) => (
                <Table.Row key={param.name}>
                  <Table.Cell className="text-[11px] text-foreground font-medium h-9">
                    {param.name}
                  </Table.Cell>
                  <Table.Cell className="text-[11px] text-muted-foreground h-9">
                    {param.description}
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table>
          </div>
        </div>

        {otherParams.length > 0 && (
          <div className="mt-3">
            <button
              type="button"
              onClick={() => setOthersExpanded((prev) => !prev)}
              className="flex items-center gap-1.5 text-xs font-medium text-subtext-color hover:text-default-font transition-colors cursor-pointer"
            >
              {othersExpanded ? (
                <FeatherChevronDown className="h-3.5 w-3.5" />
              ) : (
                <FeatherChevronRight className="h-3.5 w-3.5" />
              )}
              その他のパラメータ（{otherParams.length}）
            </button>
            {othersExpanded && (
              <div className="mt-1.5 rounded-md border border-solid border-neutral-border overflow-hidden">
                <Table
                  header={
                    <Table.HeaderRow>
                      <Table.HeaderCell className="text-[11px]">名称</Table.HeaderCell>
                      <Table.HeaderCell className="text-[11px]">説明</Table.HeaderCell>
                    </Table.HeaderRow>
                  }
                >
                  {otherParams.map((param) => (
                    <Table.Row key={param.name}>
                      <Table.Cell className="text-[11px] text-foreground font-medium h-9">
                        {param.name}
                      </Table.Cell>
                      <Table.Cell className="text-[11px] text-muted-foreground h-9">
                        {param.description}
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table>
              </div>
            )}
          </div>
        )}

        <h3 className="text-base font-semibold mt-6">実験設定一覧</h3>
        <div className="flex flex-col gap-3 mt-2">
          {implementation.experimentSettings.map((experiment) => (
            <ExperimentCard key={experiment.id} experiment={experiment} onRun={onRunExperiment} />
          ))}
          <button
            type="button"
            className="flex items-center justify-center rounded-lg border-2 border-dashed border-neutral-300 bg-transparent py-6 text-neutral-400 hover:border-neutral-400 hover:text-neutral-500 transition-colors cursor-pointer"
          >
            <FeatherPlus className="h-5 w-5" />
          </button>
        </div>
      </div>
    </>
  );
}
