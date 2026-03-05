"use client";

import { CheckCircle2, ChevronDown, Clock, History, XCircle } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import type { ResearchSection } from "@/types/research";

interface SessionDropdownProps {
  sessions: ResearchSection[];
  activeSession: ResearchSection | null;
  onSelectSession: (section: ResearchSection) => void;
  onRefreshSessions: (preferredId?: string) => Promise<void>;
}

export function SessionDropdown({
  sessions,
  activeSession,
  onSelectSession,
  onRefreshSessions,
}: SessionDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [isOpen]);

  const handleOpen = useCallback(() => {
    const next = !isOpen;
    setIsOpen(next);
    if (next) {
      void onRefreshSessions(activeSession?.id);
    }
  }, [isOpen, onRefreshSessions, activeSession?.id]);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={handleOpen}
        className="flex items-center gap-1.5 rounded-md bg-neutral-100 px-3 py-1.5 text-xs font-medium text-neutral-600 hover:bg-neutral-200 transition-colors cursor-pointer"
      >
        <History className="h-3.5 w-3.5" />
        Past Sessions
        <ChevronDown className={cn("h-3 w-3 transition-transform", isOpen && "rotate-180")} />
      </button>
      {isOpen && (
        <div className="absolute left-0 top-full mt-1 z-20 w-72 rounded-md border border-neutral-200 bg-white shadow-lg overflow-hidden">
          {sessions.length === 0 ? (
            <div className="px-4 py-3 text-sm text-neutral-500">No past sessions</div>
          ) : (
            <div className="max-h-64 overflow-y-auto">
              {sessions.map((session) => (
                <button
                  key={session.id}
                  type="button"
                  onClick={() => {
                    onSelectSession(session);
                    setIsOpen(false);
                  }}
                  className={cn(
                    "w-full text-left px-4 py-2.5 hover:bg-neutral-50 transition-colors border-b border-neutral-100 last:border-b-0",
                    activeSession?.id === session.id && "bg-blue-50",
                  )}
                >
                  <div className="flex items-start gap-2">
                    {session.status === "completed" ? (
                      <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 text-emerald-500 flex-shrink-0" />
                    ) : session.status === "failed" ? (
                      <XCircle className="w-3.5 h-3.5 mt-0.5 text-red-500 flex-shrink-0" />
                    ) : (
                      <Clock className="w-3.5 h-3.5 mt-0.5 text-amber-500 flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-neutral-800 truncate">
                        {session.title}
                      </p>
                      <p className="text-xs text-neutral-500">
                        {session.createdAt.toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
