/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExperimentCode } from './ExperimentCode';
import type { ExperimentHistory_Input } from './ExperimentHistory_Input';
import type { ResearchHypothesis } from './ResearchHypothesis';
import type { ResearchStudy } from './ResearchStudy';
import type { WriteLLMMapping } from './WriteLLMMapping';
export type WriteSubgraphRequestBody = {
    research_hypothesis: ResearchHypothesis;
    experiment_history: ExperimentHistory_Input;
    experiment_code: ExperimentCode;
    research_study_list: Array<ResearchStudy>;
    references_bib: string;
    writing_refinement_rounds?: number;
    llm_mapping?: (WriteLLMMapping | null);
};

