/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExecuteFullExperimentLLMMapping } from './ExecuteFullExperimentLLMMapping';
import type { GitHubConfig } from './GitHubConfig';
export type ExecuteFullRequestBody = {
    github_config: GitHubConfig;
    run_ids: Array<string>;
    github_actions_agent?: string;
    llm_mapping?: (ExecuteFullExperimentLLMMapping | null);
};

