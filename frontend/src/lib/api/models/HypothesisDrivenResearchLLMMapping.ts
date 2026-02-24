/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnalyzeExperimentLLMMapping } from './AnalyzeExperimentLLMMapping';
import type { CodeGenerationGraphLLMMapping } from './CodeGenerationGraphLLMMapping';
import type { DispatchExperimentValidationLLMMapping } from './DispatchExperimentValidationLLMMapping';
import type { GenerateExperimentalDesignLLMMapping } from './GenerateExperimentalDesignLLMMapping';
import type { LaTeXGraphLLMMapping } from './LaTeXGraphLLMMapping';
import type { WriteLLMMapping } from './WriteLLMMapping';
export type HypothesisDrivenResearchLLMMapping = {
    generate_experimental_design?: (GenerateExperimentalDesignLLMMapping | null);
    code_generation?: (CodeGenerationGraphLLMMapping | null);
    dispatch_experiment_validation?: (DispatchExperimentValidationLLMMapping | null);
    analyze_experiment?: (AnalyzeExperimentLLMMapping | null);
    write?: (WriteLLMMapping | null);
    latex?: (LaTeXGraphLLMMapping | null);
};

