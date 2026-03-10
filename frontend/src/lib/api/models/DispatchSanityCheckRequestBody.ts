/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EphemeralCloudRunnerConfig } from './EphemeralCloudRunnerConfig';
import type { GitHubConfig } from './GitHubConfig';
import type { StaticRunnerConfig } from './StaticRunnerConfig';
export type DispatchSanityCheckRequestBody = {
    github_config: GitHubConfig;
    run_id: string;
    runner_config?: (StaticRunnerConfig | EphemeralCloudRunnerConfig);
};

