/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExecuteTrialExperimentLLMMapping } from './ExecuteTrialExperimentLLMMapping';
import type { GitHubConfig } from './GitHubConfig';
export type ExecuteTrialRequestBody = {
    github_config: GitHubConfig;
    github_actions_agent?: string;
    llm_mapping?: (ExecuteTrialExperimentLLMMapping | null);
};

