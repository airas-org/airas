/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExecuteTrialExperimentLLMMapping } from './ExecuteTrialExperimentLLMMapping';
import type { GitHubConfig } from './GitHubConfig';
export type ExecuteTrialRequestBody = {
    github_config: GitHubConfig;
    github_actions_agent?: ExecuteTrialRequestBody.github_actions_agent;
    llm_mapping?: (ExecuteTrialExperimentLLMMapping | null);
};
export namespace ExecuteTrialRequestBody {
    export enum github_actions_agent {
        CLAUDE_CODE = 'claude_code',
        OPEN_CODE = 'open_code',
    }
}

