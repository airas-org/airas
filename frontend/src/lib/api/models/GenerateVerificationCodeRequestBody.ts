/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GenerateVerificationCodeLLMMapping } from './GenerateVerificationCodeLLMMapping';
import type { GitHubConfigRequest } from './GitHubConfigRequest';
export type GenerateVerificationCodeRequestBody = {
    user_query: string;
    what_to_verify: string;
    experiment_settings: Record<string, string>;
    steps: Array<string>;
    modification_notes: string;
    github_config: GitHubConfigRequest;
    github_actions_agent: GenerateVerificationCodeRequestBody.github_actions_agent;
    llm_mapping?: (GenerateVerificationCodeLLMMapping | null);
    verification_id?: (string | null);
};
export namespace GenerateVerificationCodeRequestBody {
    export enum github_actions_agent {
        CLAUDE_CODE = 'claude_code',
        OPEN_CODE = 'open_code',
    }
}

