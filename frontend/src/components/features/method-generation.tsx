"use client"

import { useState } from "react"
import { Lightbulb, Sparkles, FileText, Edit3, Save } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import type { Paper, Method } from "@/types/research"
import { generateMethod } from "@/lib/api-mock"

interface MethodGenerationSectionProps {
  selectedPapers: Paper[]
  generatedMethod: Method | null
  onMethodGenerated: (method: Method) => void
  onStepExecuted?: (method: Method) => void
  onBranchCreated?: (method: Method) => void
  onSave?: () => void
}

export function MethodGenerationSection({
  selectedPapers,
  generatedMethod,
  onMethodGenerated,
  onStepExecuted,
  onBranchCreated,
  onSave,
}: MethodGenerationSectionProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [editedDescription, setEditedDescription] = useState("")
  const [isManualMode, setIsManualMode] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [manualMethodName, setManualMethodName] = useState("")
  const [manualMethodDescription, setManualMethodDescription] = useState("")
  const [hasExecuted, setHasExecuted] = useState(false)
  const [tempMethod, setTempMethod] = useState<Method | null>(null)

  const handleGenerate = async () => {
    if (selectedPapers.length === 0) return
    setIsGenerating(true)
    try {
      const method = await generateMethod(selectedPapers.map((p) => p.id))
      setTempMethod(method)
      setEditedDescription(method.description)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleConfirmGenerated = () => {
    if (!tempMethod) return
    const methodToSave = { ...tempMethod, description: editedDescription }
    onMethodGenerated(methodToSave)
    if (!hasExecuted && onStepExecuted) {
      onStepExecuted(methodToSave)
      setHasExecuted(true)
    }
    setTempMethod(null)
  }

  const handleDescriptionChange = (value: string) => {
    setEditedDescription(value)
    if (tempMethod) {
      setTempMethod({ ...tempMethod, description: value })
    }
  }

  const handleManualSave = () => {
    if (!manualMethodName.trim() || !manualMethodDescription.trim()) return
    const manualMethod: Method = {
      id: "manual-" + Date.now(),
      name: manualMethodName,
      description: manualMethodDescription,
      basedOn: [],
    }
    onMethodGenerated(manualMethod)
    setEditedDescription(manualMethodDescription)
    setIsEditing(false)
    if (!hasExecuted && onStepExecuted) {
      onStepExecuted(manualMethod)
      setHasExecuted(true)
    } else if (hasExecuted && onBranchCreated) {
      onBranchCreated(manualMethod)
    }
  }

  const handleEdit = () => {
    setIsEditing(true)
    if (generatedMethod) {
      setManualMethodName(generatedMethod.name)
      setManualMethodDescription(generatedMethod.description)
    }
  }

  const handleSaveEdit = () => {
    if (!manualMethodName.trim() || !manualMethodDescription.trim()) return
    const updatedMethod: Method = {
      id: "edited-" + Date.now(),
      name: manualMethodName,
      description: manualMethodDescription,
      basedOn: generatedMethod?.basedOn || [],
    }
    onMethodGenerated(updatedMethod)
    setIsEditing(false)
    if (onBranchCreated) {
      onBranchCreated(updatedMethod)
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-blue-700 flex items-center justify-center">
          <Lightbulb className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-foreground">新規手法の生成</h3>
          <p className="text-sm text-muted-foreground">選択した論文から新しい研究手法を生成</p>
        </div>
      </div>

      {!generatedMethod && !tempMethod && (
        <div className="flex gap-2 mb-6">
          <Button
            variant={!isManualMode ? "default" : "outline"}
            size="sm"
            onClick={() => setIsManualMode(false)}
            className={!isManualMode ? "bg-blue-700 hover:bg-blue-800 text-white" : "bg-transparent"}
          >
            論文から生成
          </Button>
          <Button
            variant={isManualMode ? "default" : "outline"}
            size="sm"
            onClick={() => setIsManualMode(true)}
            className={isManualMode ? "bg-blue-700 hover:bg-blue-800 text-white" : "bg-transparent"}
          >
            手動で入力
          </Button>
        </div>
      )}

      {isManualMode && !generatedMethod && !tempMethod && (
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-foreground mb-2 block">手法名</label>
            <Input
              value={manualMethodName}
              onChange={(e) => setManualMethodName(e.target.value)}
              placeholder="例: Attention-based Graph Neural Network"
              className="bg-background"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-foreground mb-2 block">手法の説明</label>
            <Textarea
              value={manualMethodDescription}
              onChange={(e) => setManualMethodDescription(e.target.value)}
              placeholder="手法の詳細な説明を入力してください..."
              className="min-h-[200px] font-mono text-sm bg-background"
            />
          </div>
          <Button
            onClick={handleManualSave}
            disabled={!manualMethodName.trim() || !manualMethodDescription.trim()}
            className="w-full bg-blue-700 hover:bg-blue-800 text-white"
          >
            <Save className="w-4 h-4 mr-2" />
            保存
          </Button>
        </div>
      )}

      {!isManualMode && !generatedMethod && !tempMethod && (
        <>
          {selectedPapers.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>先に論文を選択するか、手動入力モードを使用してください</p>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <p className="text-sm text-muted-foreground mb-3">
                  {selectedPapers.length} 件の論文を基に新規手法を生成します:
                </p>
                <div className="flex flex-wrap gap-2">
                  {selectedPapers.map((paper) => (
                    <span key={paper.id} className="px-3 py-1 bg-muted rounded-full text-sm text-foreground">
                      {paper.title.substring(0, 30)}...
                    </span>
                  ))}
                </div>
              </div>
              <Button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full bg-blue-700 hover:bg-blue-800 text-white"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                {isGenerating ? "生成中..." : "新規手法を生成"}
              </Button>
            </>
          )}
        </>
      )}

      {tempMethod && !generatedMethod && (
        <div className="space-y-4">
          <div className="p-4 bg-muted/50 border border-border rounded-lg">
            <p className="text-sm text-muted-foreground mb-2">生成された手法（プレビュー）</p>
            <p className="text-lg font-semibold text-foreground mb-2">{tempMethod.name}</p>
            <div>
              <label className="text-sm font-medium text-foreground mb-2 block">手法の説明（編集可能）</label>
              <Textarea
                value={editedDescription}
                onChange={(e) => handleDescriptionChange(e.target.value)}
                className="min-h-[200px] font-mono text-sm bg-background"
              />
            </div>
          </div>
          <Button onClick={handleConfirmGenerated} className="w-full bg-blue-700 hover:bg-blue-800 text-white">
            <Save className="w-4 h-4 mr-2" />
            この手法を確定
          </Button>
        </div>
      )}

      {generatedMethod && (
        <div className="space-y-4">
          {isEditing ? (
            <>
              <div>
                <label className="text-sm font-medium text-foreground mb-2 block">手法名</label>
                <Input
                  value={manualMethodName}
                  onChange={(e) => setManualMethodName(e.target.value)}
                  className="bg-background"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground mb-2 block">手法の説明</label>
                <Textarea
                  value={manualMethodDescription}
                  onChange={(e) => setManualMethodDescription(e.target.value)}
                  className="min-h-[300px] font-mono text-sm bg-background"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setIsEditing(false)} className="bg-transparent">
                  キャンセル
                </Button>
                <Button onClick={handleSaveEdit} className="bg-blue-700 hover:bg-blue-800 text-white">
                  <Save className="w-4 h-4 mr-2" />
                  保存
                </Button>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-foreground">手法名</label>
                <Button variant="ghost" size="sm" onClick={handleEdit}>
                  <Edit3 className="w-4 h-4 mr-1" />
                  編集
                </Button>
              </div>
              <p className="text-lg font-semibold text-foreground">{generatedMethod.name}</p>
              <div>
                <label className="text-sm font-medium text-foreground mb-2 block">手法の説明</label>
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm text-foreground whitespace-pre-wrap">{generatedMethod.description}</p>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </Card>
  )
}
