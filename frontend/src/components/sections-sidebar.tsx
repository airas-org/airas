"use client"

import { Plus, FolderOpen, CheckCircle2, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { ResearchSection } from "@/types/research"
import { cn } from "@/lib/utils"

interface SectionsSidebarProps {
  sections: ResearchSection[]
  activeSection: ResearchSection | null
  onSelectSection: (section: ResearchSection) => void
  onCreateSection: () => void
}

export function SectionsSidebar({ sections, activeSection, onSelectSection, onCreateSection }: SectionsSidebarProps) {
  return (
    <div className="w-72 border-r border-border bg-card flex flex-col">
      <div className="p-4 border-b border-border">
        <h1 className="text-lg font-semibold text-foreground">ML Research</h1>
        <p className="text-sm text-muted-foreground">Automation Platform</p>
      </div>

      <div className="p-3">
        <Button onClick={onCreateSection} className="w-full">
          <Plus className="w-4 h-4 mr-2" />
          New Section
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => onSelectSection(section)}
              className={cn(
                "w-full text-left p-3 rounded-lg transition-colors",
                activeSection?.id === section.id
                  ? "bg-muted text-foreground"
                  : "hover:bg-muted/50 text-muted-foreground",
              )}
            >
              <div className="flex items-start gap-3">
                <FolderOpen className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{section.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    {section.status === "completed" ? (
                      <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                    ) : (
                      <Clock className="w-3 h-3 text-amber-500" />
                    )}
                    <span className="text-xs text-muted-foreground">{section.createdAt.toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
