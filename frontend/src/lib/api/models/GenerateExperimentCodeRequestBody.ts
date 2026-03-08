/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type GenerateExperimentCodeRequestBody = {
    user_query: string;
    what_to_verify: string;
    experiment_settings: Record<string, Record<string, any>>;
    steps: Array<string>;
    modification_notes: string;
    repository_name: string;
    github_owner: string;
    branch_name: string;
    github_actions_agent: GenerateExperimentCodeRequestBody.github_actions_agent;
};
export namespace GenerateExperimentCodeRequestBody {
    export enum github_actions_agent {
        CLAUDE_CODE = 'claude_code',
        OPEN_CODE = 'open_code',
    }
}

