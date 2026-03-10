/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ComputeEnvironment } from './ComputeEnvironment';
import type { GenerateExperimentalDesignLLMMapping } from './GenerateExperimentalDesignLLMMapping';
import type { ResearchHypothesis } from './ResearchHypothesis';
export type GenerateExperimentalDesignSubgraphRequestBody = {
    research_hypothesis: ResearchHypothesis;
    compute_environment: ComputeEnvironment;
    num_models_to_use: number;
    num_datasets_to_use: number;
    num_comparative_methods: number;
    llm_mapping?: (GenerateExperimentalDesignLLMMapping | null);
};

