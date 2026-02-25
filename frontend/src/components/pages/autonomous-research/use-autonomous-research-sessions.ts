import type { Dispatch, SetStateAction } from "react";
import { useCallback } from "react";
import type { AutonomousSubNav } from "@/components/main-content";
import {
  type HypothesisDrivenResearchListItemResponse,
  HypothesisDrivenResearchService,
  Status as HypothesisDrivenResearchStatus,
  type TopicOpenEndedResearchListItemResponse,
  TopicOpenEndedResearchService,
  Status as TopicOpenEndedResearchStatus,
} from "@/lib/api";
import type { ResearchSection } from "@/types/research";

export type AutonomousSectionsMap = Record<AutonomousSubNav, ResearchSection[]>;
export type AutonomousActiveSectionMap = Record<AutonomousSubNav, ResearchSection | null>;

interface UseAutonomousResearchSessionsParams {
  setAutonomousSectionsMap: Dispatch<SetStateAction<AutonomousSectionsMap>>;
  setAutonomousActiveSectionMap: Dispatch<SetStateAction<AutonomousActiveSectionMap>>;
}

const mapTopicRecord = (record: TopicOpenEndedResearchListItemResponse): ResearchSection => {
  const createdAt = new Date(record.created_at);
  return {
    id: record.id,
    title: record.title || "Untitled Research",
    createdAt: Number.isNaN(createdAt.valueOf()) ? new Date() : createdAt,
    status: record.status === TopicOpenEndedResearchStatus.COMPLETED ? "completed" : "in-progress",
  };
};

const mapHypothesisRecord = (record: HypothesisDrivenResearchListItemResponse): ResearchSection => {
  const createdAt = new Date(record.created_at);
  return {
    id: record.id,
    title: record.title || "Untitled Research",
    createdAt: Number.isNaN(createdAt.valueOf()) ? new Date() : createdAt,
    status:
      record.status === HypothesisDrivenResearchStatus.COMPLETED ? "completed" : "in-progress",
  };
};

export const useAutonomousResearchSessions = ({
  setAutonomousSectionsMap,
  setAutonomousActiveSectionMap,
}: UseAutonomousResearchSessionsParams) => {
  const fetchSections = useCallback(
    async (subNav: AutonomousSubNav, preferredId?: string) => {
      try {
        const sections =
          subNav === "topic-driven"
            ? (
                await TopicOpenEndedResearchService.listTopicOpenEndedResearchAirasV1TopicOpenEndedResearchGet()
              ).items
                .map(mapTopicRecord)
                .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime())
            : (
                await HypothesisDrivenResearchService.listHypothesisDrivenResearchAirasV1HypothesisDrivenResearchGet()
              ).items
                .map(mapHypothesisRecord)
                .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());

        setAutonomousSectionsMap((prev) => ({ ...prev, [subNav]: sections }));
        setAutonomousActiveSectionMap((prev) => {
          const current = prev[subNav];
          const next = preferredId
            ? (sections.find((s) => s.id === preferredId) ?? sections[0] ?? null)
            : current
              ? (sections.find((s) => s.id === current.id) ?? sections[0] ?? null)
              : (sections[0] ?? null);
          return { ...prev, [subNav]: next };
        });
      } catch (error) {
        console.error(`Failed to load ${subNav} research sessions`, error);
      }
    },
    [setAutonomousSectionsMap, setAutonomousActiveSectionMap],
  );

  return { fetchSections };
};
