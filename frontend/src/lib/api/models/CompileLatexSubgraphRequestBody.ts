/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CompileLatexLLMMapping } from './CompileLatexLLMMapping';
import type { GitHubConfig } from './GitHubConfig';
export type CompileLatexSubgraphRequestBody = {
    github_config: GitHubConfig;
    latex_template_name?: CompileLatexSubgraphRequestBody.latex_template_name;
    github_actions_agent?: CompileLatexSubgraphRequestBody.github_actions_agent;
    llm_mapping?: (CompileLatexLLMMapping | null);
};
export namespace CompileLatexSubgraphRequestBody {
    export enum latex_template_name {
        ICLR2024 = 'iclr2024',
        AGENTS4SCIENCE_2025 = 'agents4science_2025',
    }
    export enum github_actions_agent {
        CLAUDE_CODE = 'claude_code',
        OPEN_CODE = 'open_code',
    }
}

