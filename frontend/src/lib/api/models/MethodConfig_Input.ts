/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { OptunaConfig } from "./OptunaConfig";
import type { TrainingConfig } from "./TrainingConfig";
export type MethodConfig_Input = {
  /**
   * Name of the method (e.g., 'Proposed-v1', 'BERT-Baseline')
   */
  method_name: string;
  /**
   * Brief description of the method mechanism
   */
  description: string;
  /**
   * Training hyperparameters for this method
   */
  training_config?: TrainingConfig | null;
  /**
   * Hyperparameter search configuration for this method (includes search spaces and trial settings)
   */
  optuna_config?: OptunaConfig | null;
};
