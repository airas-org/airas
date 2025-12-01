"use client"

import { useState } from "react"
import { Play, CheckCircle2, Clock, XCircle, Loader2, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import type { ExperimentConfig, ExperimentResult } from "@/types/research"
import { runGitHubActions, getExperimentResults } from "@/lib/api-mock"
import { cn } from "@/lib/utils"

interface ExperimentRunSectionProps {
  configs: ExperimentConfig[]
  results: ExperimentResult[]
  onResultsChange: (results: ExperimentResult[]) => void
  onStepExecuted?: (results: ExperimentResult[]) => void
  onSave?: () => void
}

export function ExperimentRunSection({
  configs,
  results,
  onResultsChange,
  onStepExecuted,
  onSave,
}: ExperimentRunSectionProps) {
  const [runningExperiments, setRunningExperiments] = useState<Set<string>>(new Set())
  const [isConfirmed, setIsConfirmed] = useState(false)

  const runExperiment = async (configId: string) => {
    setRunningExperiments((prev) => new Set([...prev, configId]))
    try {
      const { runId } = await runGitHubActions("repo-1", configId)
      const result = await getExperimentResults(runId)
      const newResults = [...results.filter((r) => r.configId !== configId), result]
      onResultsChange(newResults)
    } finally {
      setRunningExperiments((prev) => {
        const next = new Set(prev)
        next.delete(configId)
        return next
      })
    }
  }

  const runAllExperiments = async () => {
    for (const config of configs) {
      await runExperiment(config.id)
    }
  }

  const handleConfirm = () => {
    setIsConfirmed(true)
    if (onStepExecuted) {
      onStepExecuted(results)
    }
    if (onSave) {
      onSave()
    }
  }

  const getResult = (configId: string) => results.find((r) => r.configId === configId)

  const completedResults = results.filter((r) => r.status === "completed")
  const allCompleted = configs.length > 0 && completedResults.length === configs.length

  const StatusIcon = ({ status }: { status?: string }) => {
    if (status === "completed") return <CheckCircle2 className="w-5 h-5 text-blue-700" />
    if (status === "failed") return <XCircle className="w-5 h-5 text-destructive" />
    if (status === "running") return <Loader2 className="w-5 h-5 text-blue-700 animate-spin" />
    return <Clock className="w-5 h-5 text-muted-foreground" />
  }

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-blue-700 flex items-center justify-center">
          <Play className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-foreground">実験の実行</h3>
          <p className="text-sm text-muted-foreground">GitHub Actionsで実験を実行</p>
        </div>
      </div>

      {configs.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <Play className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>先に実験コードを生成してください</p>
        </div>
      ) : (
        <>
          <div className="mb-4">
            <Button
              onClick={runAllExperiments}
              disabled={runningExperiments.size > 0}
              className="w-full bg-blue-700 hover:bg-blue-800 text-white"
            >
              {runningExperiments.size > 0 ? "実行中..." : "全ての実験を実行"}
            </Button>
          </div>

          <div className="space-y-4">
            {configs.map((config) => {
              const result = getResult(config.id)
              const isRunning = runningExperiments.has(config.id)

              return (
                <div
                  key={config.id}
                  className={cn(
                    "p-4 border rounded-lg transition-colors",
                    result?.status === "completed" ? "border-blue-700/50 bg-blue-700/10" : "border-border",
                  )}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <StatusIcon status={isRunning ? "running" : result?.status} />
                      <h4 className="font-medium text-foreground">{config.model}</h4>
                    </div>
                    {!result && !isRunning && (
                      <Button size="sm" variant="outline" onClick={() => runExperiment(config.id)}>
                        <Play className="w-3 h-3 mr-1" />
                        実行
                      </Button>
                    )}
                  </div>

                  {isRunning && (
                    <div className="space-y-2">
                      <Progress value={45} className="h-2" />
                      <p className="text-xs text-muted-foreground">実験を実行中...</p>
                    </div>
                  )}

                  {result?.status === "completed" && (
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-3">
                      {Object.entries(result.metrics).map(([key, value]) => (
                        <div key={key} className="text-center p-2 bg-card rounded">
                          <p className="text-xs text-muted-foreground uppercase">{key}</p>
                          <p className="text-lg font-semibold text-foreground">
                            {typeof value === "number" ? value.toFixed(3) : value}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {allCompleted && !isConfirmed && (
            <Button onClick={handleConfirm} className="w-full mt-4 bg-blue-700 hover:bg-blue-800 text-white">
              <Check className="w-4 h-4 mr-2" />
              この結果を確定
            </Button>
          )}

          {isConfirmed && (
            <div className="flex items-center justify-center gap-2 p-3 mt-4 bg-muted rounded-lg">
              <Check className="w-5 h-5 text-blue-700" />
              <span className="text-sm text-muted-foreground">確定済み</span>
            </div>
          )}
        </>
      )}
    </Card>
  )
}
