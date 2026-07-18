/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FetchPaperReproductionResultsLLMMapping } from './FetchPaperReproductionResultsLLMMapping';
import type { GitHubConfigRequest } from './GitHubConfigRequest';
export type FetchPaperReproductionResultsRequestBody = {
    github_config: GitHubConfigRequest;
    repro_id: string;
    llm_mapping?: (FetchPaperReproductionResultsLLMMapping | null);
};

