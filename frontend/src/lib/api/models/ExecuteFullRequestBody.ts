/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExecuteFullExperimentLLMMapping } from './ExecuteFullExperimentLLMMapping';
import type { GitHubConfig } from './GitHubConfig';
export type ExecuteFullRequestBody = {
    github_config: GitHubConfig;
    run_ids: Array<string>;
    github_actions_agent?: ExecuteFullRequestBody.github_actions_agent;
    llm_mapping?: (ExecuteFullExperimentLLMMapping | null);
};
export namespace ExecuteFullRequestBody {
    export enum github_actions_agent {
        CLAUDE_CODE = 'claude_code',
        OPEN_CODE = 'open_code',
    }
}

