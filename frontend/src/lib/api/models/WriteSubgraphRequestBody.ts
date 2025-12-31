/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExperimentalAnalysis } from "./ExperimentalAnalysis";
import type { ExperimentalDesign_Input } from "./ExperimentalDesign_Input";
import type { ExperimentalResults } from "./ExperimentalResults";
import type { ExperimentCode } from "./ExperimentCode";
import type { ResearchHypothesis } from "./ResearchHypothesis";
import type { ResearchStudy } from "./ResearchStudy";
import type { WriteLLMMapping } from "./WriteLLMMapping";
export type WriteSubgraphRequestBody = {
  research_hypothesis: ResearchHypothesis;
  experimental_design: ExperimentalDesign_Input;
  experiment_code: ExperimentCode;
  experimental_results: ExperimentalResults;
  experimental_analysis: ExperimentalAnalysis;
  research_study_list: Array<ResearchStudy>;
  references_bib: string;
  writing_refinement_rounds?: number;
  llm_mapping?: WriteLLMMapping | null;
};
