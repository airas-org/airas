/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CodeGenerationGraphLLMMapping } from './CodeGenerationGraphLLMMapping';
import type { DecideExperimentCycleLLMMapping } from './DecideExperimentCycleLLMMapping';
import type { DispatchExperimentValidationLLMMapping } from './DispatchExperimentValidationLLMMapping';
import type { RefineExperimentalDesignLLMMapping } from './RefineExperimentalDesignLLMMapping';
export type ExperimentCycleGraphLLMMapping = {
    code_generation?: (CodeGenerationGraphLLMMapping | null);
    dispatch_experiment_validation?: (DispatchExperimentValidationLLMMapping | null);
    decide_experiment_cycle?: (DecideExperimentCycleLLMMapping | null);
    refine_experimental_design?: (RefineExperimentalDesignLLMMapping | null);
};

