/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CompileLatexLLMMapping } from './CompileLatexLLMMapping';
import type { GitHubConfig } from './GitHubConfig';
export type CompileLatexSubgraphRequestBody = {
    github_config: GitHubConfig;
    latex_template_name?: CompileLatexSubgraphRequestBody.latex_template_name;
    llm_mapping?: (CompileLatexLLMMapping | null);
};
export namespace CompileLatexSubgraphRequestBody {
    export enum latex_template_name {
        ICLR2024 = 'iclr2024',
        AGENTS4SCIENCE_2025 = 'agents4science_2025',
        MDPI = 'mdpi',
    }
}

