/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GitHubConfigRequest } from './GitHubConfigRequest';
export type DispatchParameterTuningRunRequestBody = {
    github_config: GitHubConfigRequest;
    repro_id: string;
    repo_url?: string;
    runner_label?: (Array<string> | null);
};

