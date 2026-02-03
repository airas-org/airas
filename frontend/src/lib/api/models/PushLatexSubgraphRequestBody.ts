/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GitHubConfig } from './GitHubConfig';
export type PushLatexSubgraphRequestBody = {
    github_config: GitHubConfig;
    latex_text: string;
    latex_template_name?: PushLatexSubgraphRequestBody.latex_template_name;
};
export namespace PushLatexSubgraphRequestBody {
    export enum latex_template_name {
        ICLR2024 = 'iclr2024',
        AGENTS4SCIENCE_2025 = 'agents4science_2025',
        MDPI = 'MDPI',
    }
}

