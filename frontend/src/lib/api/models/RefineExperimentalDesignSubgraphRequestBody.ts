/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ComputeEnvironment } from './ComputeEnvironment';
import type { ExperimentHistory_Input } from './ExperimentHistory_Input';
import type { RefineExperimentalDesignLLMMapping } from './RefineExperimentalDesignLLMMapping';
import type { ResearchHypothesis } from './ResearchHypothesis';
export type RefineExperimentalDesignSubgraphRequestBody = {
    research_hypothesis: ResearchHypothesis;
    experiment_history: ExperimentHistory_Input;
    design_instruction: string;
    compute_environment: ComputeEnvironment;
    num_models_to_use: number;
    num_datasets_to_use: number;
    num_comparative_methods: number;
    llm_mapping?: (RefineExperimentalDesignLLMMapping | null);
};

