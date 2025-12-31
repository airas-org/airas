/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GenerateExperimentalDesignLLMMapping } from "./GenerateExperimentalDesignLLMMapping";
import type { ResearchHypothesis } from "./ResearchHypothesis";
import type { RunnerConfig } from "./RunnerConfig";
export type GenerateExperimentalDesignSubgraphRequestBody = {
  research_hypothesis: ResearchHypothesis;
  runner_config: RunnerConfig;
  num_models_to_use: number;
  num_datasets_to_use: number;
  num_comparative_methods: number;
  llm_mapping?: GenerateExperimentalDesignLLMMapping | null;
};
