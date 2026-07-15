/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExperimentCycleGraphLLMMapping } from './ExperimentCycleGraphLLMMapping';
import type { GenerateExperimentalDesignLLMMapping } from './GenerateExperimentalDesignLLMMapping';
import type { LaTeXGraphLLMMapping } from './LaTeXGraphLLMMapping';
import type { WriteLLMMapping } from './WriteLLMMapping';
export type HypothesisDrivenResearchLLMMapping = {
    generate_experimental_design?: (GenerateExperimentalDesignLLMMapping | null);
    experiment_cycle?: (ExperimentCycleGraphLLMMapping | null);
    write?: (WriteLLMMapping | null);
    latex?: (LaTeXGraphLLMMapping | null);
};

