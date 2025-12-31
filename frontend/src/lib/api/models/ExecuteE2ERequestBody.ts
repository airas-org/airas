/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GitHubConfig } from "./GitHubConfig";
import type { RunnerConfig } from "./RunnerConfig";
import type { WandbConfig } from "./WandbConfig";
export type ExecuteE2ERequestBody = {
  github_config: GitHubConfig;
  query_list: Array<string>;
  runner_config: RunnerConfig;
  wandb_config: WandbConfig;
  is_private?: boolean;
  max_results_per_query?: number;
  refinement_rounds?: number;
  num_models_to_use?: number;
  num_datasets_to_use?: number;
  num_comparative_methods?: number;
  max_code_validations?: number;
  writing_refinement_rounds?: number;
  latex_template_name?: string;
};
