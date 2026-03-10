"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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
  listViewKey?: number;
}

export function AutonomousResearchPage({
  section,
  sessions,
  onSelectSession,
  onCreateSection,
  onUpdateSectionTitle,
  onRefreshSessions,
  listViewKey,
}: AutonomousResearchPageProps) {
  const [subView, setSubView] = useState<SubView>(section ? "detail" : "list");
  const onCreateSectionRef = useRef(onCreateSection);
  onCreateSectionRef.current = onCreateSection;

  // サイドバーからクリック時は入力画面を表示
  useEffect(() => {
    if (listViewKey !== undefined) {
      onCreateSectionRef.current();
      setSubView("input");
    }
  }, [listViewKey]);

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
      setSubView("list");
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
    />
  );
}
