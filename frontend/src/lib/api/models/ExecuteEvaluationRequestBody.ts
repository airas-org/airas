/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExecuteEvaluationLLMMapping } from './ExecuteEvaluationLLMMapping';
import type { GitHubConfig } from './GitHubConfig';
export type ExecuteEvaluationRequestBody = {
    github_config: GitHubConfig;
    github_actions_agent?: ExecuteEvaluationRequestBody.github_actions_agent;
    llm_mapping?: (ExecuteEvaluationLLMMapping | null);
};
export namespace ExecuteEvaluationRequestBody {
    export enum github_actions_agent {
        CLAUDE_CODE = 'claude_code',
        OPEN_CODE = 'open_code',
    }
}

