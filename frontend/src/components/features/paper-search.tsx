"use client"

import { useState } from "react"
import { Search, Check, Users, Calendar, Quote, Save } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { Paper } from "@/types/research"
import { searchPapers } from "@/lib/api-mock"
import { cn } from "@/lib/utils"

interface PaperSearchSectionProps {
  selectedPapers: Paper[]
  onPapersChange: (papers: Paper[]) => void
  onStepExecuted?: (papers: Paper[]) => void
  onSave?: () => void
}

export function PaperSearchSection({
  selectedPapers,
  onPapersChange,
  onStepExecuted,
  onSave,
}: PaperSearchSectionProps) {
  const [query, setQuery] = useState("")
  const [papers, setPapers] = useState<Paper[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [hasExecuted, setHasExecuted] = useState(false)
  const [tempSelectedPapers, setTempSelectedPapers] = useState<Paper[]>([])

  const handleSearch = async () => {
    if (!query.trim()) return
    setIsSearching(true)
    try {
      const results = await searchPapers(query)
      setPapers(results)
      setTempSelectedPapers(selectedPapers)
    } finally {
      setIsSearching(false)
    }
  }

  const togglePaper = (paper: Paper) => {
    const isSelected = tempSelectedPapers.some((p) => p.id === paper.id)
    if (isSelected) {
      setTempSelectedPapers(tempSelectedPapers.filter((p) => p.id !== paper.id))
    } else {
      setTempSelectedPapers([...tempSelectedPapers, paper])
    }
  }

  const handleConfirmSelection = () => {
    onPapersChange(tempSelectedPapers)
    if (!hasExecuted && onStepExecuted) {
      onStepExecuted(tempSelectedPapers)
      setHasExecuted(true)
    } else if (hasExecuted && onSave) {
      onSave()
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
          <Search className="w-5 h-5 text-primary-foreground" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-foreground">論文取得</h3>
          <p className="text-sm text-muted-foreground">関連する研究論文を検索・選択</p>
        </div>
      </div>

      <div className="flex gap-3 mb-6">
        <Input
          placeholder="検索キーワードを入力..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="flex-1"
        />
        <Button onClick={handleSearch} disabled={isSearching}>
          {isSearching ? "検索中..." : "検索"}
        </Button>
      </div>

      {papers.length > 0 && (
        <div className="grid gap-4">
          {papers.map((paper) => {
            const isSelected = tempSelectedPapers.some((p) => p.id === paper.id)
            return (
              <button
                key={paper.id}
                onClick={() => togglePaper(paper)}
                className={cn(
                  "w-full text-left p-4 rounded-lg border-2 transition-all",
                  isSelected ? "border-primary bg-muted" : "border-border hover:border-muted-foreground",
                )}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-medium text-foreground">{paper.title}</h4>
                      {isSelected && (
                        <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                          <Check className="w-3 h-3 text-primary-foreground" />
                        </div>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{paper.abstract}</p>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        {paper.authors.slice(0, 2).join(", ")}
                        {paper.authors.length > 2 && " et al."}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {paper.year}
                      </span>
                      <span className="flex items-center gap-1">
                        <Quote className="w-3 h-3" />
                        {paper.citations.toLocaleString()} citations
                      </span>
                    </div>
                  </div>
                  <Badge variant="secondary" className="shrink-0">
                    {Math.round(paper.relevanceScore * 100)}% match
                  </Badge>
                </div>
              </button>
            )
          })}
        </div>
      )}

      {papers.length > 0 && (
        <div className="mt-6 pt-6 border-t border-border flex items-center justify-between">
          <p className="text-sm text-muted-foreground">{tempSelectedPapers.length} 件の論文を選択中</p>
          <Button
            onClick={handleConfirmSelection}
            disabled={tempSelectedPapers.length === 0}
            className="bg-blue-700 hover:bg-blue-800 text-white"
          >
            <Save className="w-4 h-4 mr-2" />
            選択を確定
          </Button>
        </div>
      )}

      {selectedPapers.length > 0 && papers.length === 0 && (
        <div className="mt-6 pt-6 border-t border-border">
          <p className="text-sm text-muted-foreground mb-2">確定済み: {selectedPapers.length} 件の論文</p>
          <div className="flex flex-wrap gap-2">
            {selectedPapers.map((paper) => (
              <span key={paper.id} className="px-3 py-1 bg-muted rounded-full text-sm text-foreground">
                {paper.title.substring(0, 30)}...
              </span>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}
