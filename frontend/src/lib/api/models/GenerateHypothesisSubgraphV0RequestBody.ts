/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GenerateHypothesisSubgraphV0LLMMapping } from './GenerateHypothesisSubgraphV0LLMMapping';
import type { ResearchStudy } from './ResearchStudy';
export type GenerateHypothesisSubgraphV0RequestBody = {
    research_topic: string;
    research_study_list: Array<ResearchStudy>;
    refinement_rounds: number;
    llm_mapping?: (GenerateHypothesisSubgraphV0LLMMapping | null);
};

