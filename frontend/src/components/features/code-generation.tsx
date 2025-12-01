"use client"

import { useState, useEffect } from "react"
import { Code2, Github, ExternalLink, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import type { ExperimentConfig } from "@/types/research"
import { generateExperimentCode, createGitHubRepo, pushToGitHub } from "@/lib/api-mock"

interface CodeGenerationSectionProps {
  configs: ExperimentConfig[]
  githubUrl: string | null
  onGithubUrlChange: (url: string | null) => void
  onStepExecuted?: (url: string) => void
  onSave?: () => void
}

export function CodeGenerationSection({
  configs,
  githubUrl,
  onGithubUrlChange,
  onStepExecuted,
  onSave,
}: CodeGenerationSectionProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedCode, setGeneratedCode] = useState<string | null>(null)
  const [isPushing, setIsPushing] = useState(false)
  const [isConfirmed, setIsConfirmed] = useState(false)
  const [prevConfigIds, setPrevConfigIds] = useState<string[]>([])

  useEffect(() => {
    const currentConfigIds = configs
      .map((c) => c.id)
      .sort()
      .join(",")
    const prevIds = prevConfigIds.join(",")

    if (configs.length === 0) {
      setGeneratedCode(null)
      setIsConfirmed(false)
      setPrevConfigIds([])
    } else if (currentConfigIds !== prevIds && prevIds !== "") {
      setGeneratedCode(null)
      setIsConfirmed(false)
      setPrevConfigIds(configs.map((c) => c.id))
    } else if (prevIds === "") {
      setPrevConfigIds(configs.map((c) => c.id))
    }
  }, [configs])

  useEffect(() => {
    if (!githubUrl) {
      setIsConfirmed(false)
    }
  }, [githubUrl])

  const handleGenerate = async () => {
    if (configs.length === 0) return
    setIsGenerating(true)
    try {
      const code = await generateExperimentCode(configs[0])
      setGeneratedCode(code)
    } finally {
      setIsGenerating(false)
    }
  }

  const handlePushToGitHub = async () => {
    if (!generatedCode) return
    setIsPushing(true)
    try {
      const repo = await createGitHubRepo("ml-experiment-" + Date.now())
      await pushToGitHub(repo.repoId, generatedCode)
      onGithubUrlChange(repo.url)
    } finally {
      setIsPushing(false)
    }
  }

  const handleConfirm = () => {
    if (!githubUrl) return
    setIsConfirmed(true)
    if (onStepExecuted) {
      onStepExecuted(githubUrl)
    }
    if (onSave) {
      onSave()
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-blue-700 flex items-center justify-center">
          <Code2 className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-foreground">実験コードの生成</h3>
          <p className="text-sm text-muted-foreground">実験設定からコードを生成しGitHubへ送信</p>
        </div>
      </div>

      {configs.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <Code2 className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>先に実験設定を作成してください</p>
        </div>
      ) : (
        <>
          {!generatedCode && (
            <Button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full bg-blue-700 hover:bg-blue-800 text-white"
            >
              {isGenerating ? "生成中..." : "実験コードを生成"}
            </Button>
          )}

          {generatedCode && (
            <div className="space-y-4">
              <div className="bg-secondary rounded-lg p-4 overflow-x-auto">
                <pre className="text-sm text-secondary-foreground font-mono whitespace-pre-wrap">{generatedCode}</pre>
              </div>

              {!githubUrl ? (
                <Button onClick={handlePushToGitHub} disabled={isPushing} className="w-full">
                  <Github className="w-4 h-4 mr-2" />
                  {isPushing ? "送信中..." : "GitHubへ送信"}
                </Button>
              ) : (
                <div className="space-y-4">
                  <div className="p-4 bg-blue-700/10 border border-blue-700/20 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Check className="w-5 h-5 text-blue-700" />
                      <span className="font-medium text-foreground">GitHubに送信完了</span>
                    </div>
                    <a
                      href={githubUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-blue-700 hover:underline"
                    >
                      <Github className="w-4 h-4" />
                      {githubUrl}
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  {!isConfirmed ? (
                    <Button onClick={handleConfirm} className="w-full bg-blue-700 hover:bg-blue-800 text-white">
                      <Check className="w-4 h-4 mr-2" />
                      このコードを確定
                    </Button>
                  ) : (
                    <div className="flex items-center justify-center gap-2 p-3 bg-muted rounded-lg">
                      <Check className="w-5 h-5 text-blue-700" />
                      <span className="text-sm text-muted-foreground">確定済み</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </Card>
  )
}
