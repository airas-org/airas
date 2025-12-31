/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnalyzeExperimentLLMMapping } from "./AnalyzeExperimentLLMMapping";
import type { ExperimentalDesign_Input } from "./ExperimentalDesign_Input";
import type { ExperimentalResults } from "./ExperimentalResults";
import type { ExperimentCode } from "./ExperimentCode";
import type { ResearchHypothesis } from "./ResearchHypothesis";
export type AnalyzeExperimentRequestBody = {
  research_hypothesis: ResearchHypothesis;
  experimental_design: ExperimentalDesign_Input;
  experiment_code: ExperimentCode;
  experimental_results: ExperimentalResults;
  llm_mapping?: AnalyzeExperimentLLMMapping | null;
};
