/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DispatchDiagramGenerationLLMMapping } from './DispatchDiagramGenerationLLMMapping';
import type { GitHubConfig } from './GitHubConfig';
export type DispatchDiagramGenerationRequestBody = {
    github_config: GitHubConfig;
    github_actions_agent?: DispatchDiagramGenerationRequestBody.github_actions_agent;
    diagram_description?: (string | null);
    prompt_path?: (string | null);
    llm_mapping?: (DispatchDiagramGenerationLLMMapping | null);
};
export namespace DispatchDiagramGenerationRequestBody {
    export enum github_actions_agent {
        CLAUDE_CODE = 'claude_code',
        OPEN_CODE = 'open_code',
    }
}

