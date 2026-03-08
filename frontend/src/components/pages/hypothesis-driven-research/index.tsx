"use client";

import { useCallback, useEffect, useState } from "react";
import type { ResearchSection } from "@/types/research";
import { HypothesisDrivenDetail } from "./hypothesis-driven-detail";
import { HypothesisDrivenInput } from "./hypothesis-driven-input";
import { HypothesisDrivenList } from "./hypothesis-driven-list";

type SubView = "list" | "input" | "detail";

interface HypothesisDrivenResearchPageProps {
  section: ResearchSection | null;
  sessions: ResearchSection[];
  onSelectSession: (section: ResearchSection) => void;
  onCreateSection: () => void;
  onUpdateSectionTitle: (title: string) => void;
  onRefreshSessions: (preferredId?: string) => Promise<void>;
}

export function HypothesisDrivenResearchPage({
  section,
  sessions,
  onSelectSession,
  onCreateSection,
  onUpdateSectionTitle,
  onRefreshSessions,
}: HypothesisDrivenResearchPageProps) {
  const [subView, setSubView] = useState<SubView>(section ? "detail" : "list");

  const handleSelectSession = useCallback(
    (s: ResearchSection) => {
      onSelectSession(s);
      setSubView("detail");
    },
    [onSelectSession],
  );

  const handleNavigateToInput = useCallback(() => {
    onCreateSection();
    setSubView("input");
  }, [onCreateSection]);

  const handleBackToList = useCallback(() => {
    setSubView("list");
  }, []);

  useEffect(() => {
    if (subView === "list") {
      void onRefreshSessions();
    }
  }, [subView, onRefreshSessions]);

  const handleResearchStarted = useCallback(
    async (taskId: string) => {
      await onRefreshSessions(taskId);
      setSubView("detail");
    },
    [onRefreshSessions],
  );

  if (subView === "input") {
    return (
      <HypothesisDrivenInput onBack={handleBackToList} onResearchStarted={handleResearchStarted} />
    );
  }

  if (subView === "detail" && section) {
    return (
      <HypothesisDrivenDetail
        section={section}
        onBack={handleBackToList}
        onUpdateSectionTitle={onUpdateSectionTitle}
        onRefreshSessions={onRefreshSessions}
      />
    );
  }

  return (
    <HypothesisDrivenList
      sessions={sessions}
      onSelectSession={handleSelectSession}
      onNavigateToInput={handleNavigateToInput}
    />
  );
}
