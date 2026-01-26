import type { Dispatch, SetStateAction } from "react";
import { useCallback } from "react";
import {
  type TopicOpenEndedResearchListItemResponse,
  TopicOpenEndedResearchService,
  Status as TopicOpenEndedResearchStatus,
} from "@/lib/api";
import type { ResearchSection } from "@/types/research";

interface UseAutonomousResearchSessionsParams {
  setAutoSections: Dispatch<SetStateAction<ResearchSection[]>>;
  setActiveAutoSection: Dispatch<SetStateAction<ResearchSection | null>>;
}

const mapAutoResearchRecordToSection = (
  record: TopicOpenEndedResearchListItemResponse,
): ResearchSection => {
  const createdAt = new Date(record.created_at);
  return {
    id: record.id,
    title: record.title || "Untitled Research",
    createdAt: Number.isNaN(createdAt.valueOf()) ? new Date() : createdAt,
    status: record.status === TopicOpenEndedResearchStatus.COMPLETED ? "completed" : "in-progress",
  };
};

export const useAutonomousResearchSessions = ({
  setAutoSections,
  setActiveAutoSection,
}: UseAutonomousResearchSessionsParams) => {
  const fetchAutoSections = useCallback(
    async (preferredId?: string) => {
      try {
        const response =
          await TopicOpenEndedResearchService.listTopicOpenEndedResearchAirasV1TopicOpenEndedResearchGet();
        const sections = response.items
          .map(mapAutoResearchRecordToSection)
          .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
        setAutoSections(sections);
        setActiveAutoSection((prev) => {
          if (preferredId) {
            return sections.find((section) => section.id === preferredId) ?? sections[0] ?? null;
          }
          if (prev) {
            return sections.find((section) => section.id === prev.id) ?? sections[0] ?? null;
          }
          return sections[0] ?? null;
        });
      } catch (error) {
        console.error("Failed to load autonomous research sessions", error);
      }
    },
    [setActiveAutoSection, setAutoSections],
  );

  return { fetchAutoSections };
};
