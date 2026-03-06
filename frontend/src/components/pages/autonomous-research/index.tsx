"use client";

import { useCallback, useState } from "react";
import type { ResearchSection } from "@/types/research";
import { TopicDrivenDetail } from "./topic-driven-detail";
import { TopicDrivenInput } from "./topic-driven-input";
import { TopicDrivenList } from "./topic-driven-list";

type SubView = "list" | "input" | "detail";

interface AutonomousResearchPageProps {
  section: ResearchSection | null;
  sessions: ResearchSection[];
  onSelectSession: (section: ResearchSection) => void;
  onCreateSection: () => void;
  onUpdateSectionTitle: (title: string) => void;
  onRefreshSessions: (preferredId?: string) => Promise<void>;
}

export function AutonomousResearchPage({
  section,
  sessions,
  onSelectSession,
  onCreateSection,
  onUpdateSectionTitle,
  onRefreshSessions,
}: AutonomousResearchPageProps) {
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

  const handleResearchStarted = useCallback(
    async (taskId: string) => {
      await onRefreshSessions(taskId);
      setSubView("detail");
    },
    [onRefreshSessions],
  );

  if (subView === "input") {
    return <TopicDrivenInput onBack={handleBackToList} onResearchStarted={handleResearchStarted} />;
  }

  if (subView === "detail" && section) {
    return (
      <TopicDrivenDetail
        section={section}
        onBack={handleBackToList}
        onUpdateSectionTitle={onUpdateSectionTitle}
        onRefreshSessions={onRefreshSessions}
      />
    );
  }

  return (
    <TopicDrivenList
      sessions={sessions}
      onSelectSession={handleSelectSession}
      onNavigateToInput={handleNavigateToInput}
      onRefreshSessions={onRefreshSessions}
    />
  );
}
