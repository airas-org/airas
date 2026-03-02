/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GitHubConfig } from './GitHubConfig';
export type DispatchInteractiveRepoAgentRequestBody = {
    github_config: GitHubConfig;
    github_actions_agent: DispatchInteractiveRepoAgentRequestBody.github_actions_agent;
    session_username: string;
    session_password: string;
};
export namespace DispatchInteractiveRepoAgentRequestBody {
    export enum github_actions_agent {
        CLAUDE_CODE = 'claude_code',
        OPEN_CODE = 'open_code',
    }
}

