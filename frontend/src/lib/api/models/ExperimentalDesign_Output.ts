/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EvaluationMetric } from "./EvaluationMetric";
import type { MethodConfig_Output } from "./MethodConfig_Output";
import type { RunnerConfig } from "./RunnerConfig";
export type ExperimentalDesign_Output = {
  /**
   * Overall experimental design including task definition, data handling approach, and implementation details
   */
  experiment_summary?: string | null;
  /**
   * Computational environment specification
   */
  runner_config?: RunnerConfig | null;
  /**
   * Evaluation metrics with detailed calculation methods and visualizations
   */
  evaluation_metrics?: Array<EvaluationMetric> | null;
  /**
   * List of models to be used in the experiments
   */
  models_to_use?: Array<string> | null;
  /**
   * List of datasets to be used in the experiments
   */
  datasets_to_use?: Array<string> | null;
  /**
   * Configuration for the proposed method
   */
  proposed_method: MethodConfig_Output;
  /**
   * Configurations for baseline/comparative methods
   */
  comparative_methods?: Array<MethodConfig_Output> | null;
};
