import type { Dispatch, SetStateAction } from "react";
import { useCallback } from "react";
import {
  type HypothesisDrivenResearchListItemResponse,
  HypothesisDrivenResearchService,
  Status as HypothesisDrivenResearchStatus,
} from "@/lib/api";
import type { ResearchSection } from "@/types/research";

interface UseHypothesisDrivenSessionsParams {
  setHypothesisSections: Dispatch<SetStateAction<ResearchSection[]>>;
  setActiveHypothesisSection: Dispatch<SetStateAction<ResearchSection | null>>;
}

const mapHypothesisRecordToSection = (
  record: HypothesisDrivenResearchListItemResponse,
): ResearchSection => {
  const createdAt = new Date(record.created_at);
  return {
    id: record.id,
    title: record.title || "Untitled Research",
    createdAt: Number.isNaN(createdAt.valueOf()) ? new Date() : createdAt,
    status:
      record.status === HypothesisDrivenResearchStatus.COMPLETED ? "completed" : "in-progress",
  };
};

export const useHypothesisDrivenSessions = ({
  setHypothesisSections,
  setActiveHypothesisSection,
}: UseHypothesisDrivenSessionsParams) => {
  const fetchHypothesisSections = useCallback(
    async (preferredId?: string) => {
      try {
        const response =
          await HypothesisDrivenResearchService.listHypothesisDrivenResearchAirasV1HypothesisDrivenResearchGet();
        const sections = response.items
          .map(mapHypothesisRecordToSection)
          .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
        setHypothesisSections(sections);
        setActiveHypothesisSection((prev) => {
          if (preferredId) {
            return sections.find((section) => section.id === preferredId) ?? sections[0] ?? null;
          }
          if (prev) {
            return sections.find((section) => section.id === prev.id) ?? sections[0] ?? null;
          }
          return sections[0] ?? null;
        });
      } catch (error) {
        console.error("Failed to load hypothesis-driven research sessions", error);
      }
    },
    [setActiveHypothesisSection, setHypothesisSections],
  );

  return { fetchHypothesisSections };
};
