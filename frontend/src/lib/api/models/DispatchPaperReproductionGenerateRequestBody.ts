/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DispatchPaperReproductionGenerateLLMMapping } from './DispatchPaperReproductionGenerateLLMMapping';
import type { GitHubConfigRequest } from './GitHubConfigRequest';
export type DispatchPaperReproductionGenerateRequestBody = {
    github_config: GitHubConfigRequest;
    paper_url: string;
    instruction: string;
    repo_url?: string;
    github_actions_agent?: DispatchPaperReproductionGenerateRequestBody.github_actions_agent;
    runner_label?: (Array<string> | null);
    llm_mapping: DispatchPaperReproductionGenerateLLMMapping;
};
export namespace DispatchPaperReproductionGenerateRequestBody {
    export enum github_actions_agent {
        CLAUDE_CODE = 'claude_code',
        OPEN_CODE = 'open_code',
    }
}

