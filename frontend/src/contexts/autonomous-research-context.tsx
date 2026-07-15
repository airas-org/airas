import { createContext, type ReactNode, useContext } from "react";
import type { AutonomousSubNav } from "@/components/main-content";
import type {
  AutonomousActiveSectionMap,
  AutonomousSectionsMap,
} from "@/components/pages/autonomous-research/use-autonomous-research-sessions";
import type { ResearchSection } from "@/types/research";

interface AutonomousResearchContextType {
  sectionsMap: AutonomousSectionsMap;
  activeSectionMap: AutonomousActiveSectionMap;
  onSelectSession: (subNav: AutonomousSubNav, section: ResearchSection) => void;
  onCreateSection: (subNav: AutonomousSubNav) => void;
  onUpdateSectionTitle: (subNav: AutonomousSubNav, title: string) => void;
  onRefreshSessions: (subNav: AutonomousSubNav, preferredId?: string) => Promise<void>;
  listViewKey: number;
}

const AutonomousResearchContext = createContext<AutonomousResearchContextType | null>(null);

export function AutonomousResearchProvider({
  children,
  value,
}: {
  children: ReactNode;
  value: AutonomousResearchContextType;
}) {
  return (
    <AutonomousResearchContext.Provider value={value}>
      {children}
    </AutonomousResearchContext.Provider>
  );
}

export function useAutonomousResearchContext() {
  const ctx = useContext(AutonomousResearchContext);
  if (!ctx) {
    throw new Error("useAutonomousResearchContext must be used within AutonomousResearchProvider");
  }
  return ctx;
}
