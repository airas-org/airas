"use client";

import { CheckCircle2, Clock, FolderOpen } from "lucide-react";
import type { CSSProperties } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import type { ResearchSection } from "@/types/research";

interface SectionsSidebarProps {
  sections: ResearchSection[];
  activeSection: ResearchSection | null;
  onSelectSection: (section: ResearchSection) => void;
}

export function SectionsSidebar({
  sections,
  activeSection,
  onSelectSection,
}: SectionsSidebarProps) {
  const fadeMaskStyle: CSSProperties = {
    WebkitMaskImage: "linear-gradient(90deg, #000 80%, transparent)",
    maskImage: "linear-gradient(90deg, #000 80%, transparent)",
  };

  return (
    <div className="w-60 border-r border-border bg-card flex flex-col">
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {sections.map((section) => (
            <button
              key={section.id}
              type="button"
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
                  <p className="text-sm font-medium truncate" style={fadeMaskStyle}>
                    {section.title}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    {section.status === "completed" ? (
                      <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                    ) : (
                      <Clock className="w-3 h-3 text-amber-500" />
                    )}
                    <span className="text-xs text-muted-foreground">
                      {section.createdAt.toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
