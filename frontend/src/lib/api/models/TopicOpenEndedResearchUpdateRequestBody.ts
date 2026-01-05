/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Status } from './Status';
import type { StepType } from './StepType';
export type TopicOpenEndedResearchUpdateRequestBody = {
    title?: (string | null);
    status?: (Status | null);
    current_step?: (StepType | null);
    error_message?: (string | null);
    result?: (Record<string, any> | null);
    github_url?: (string | null);
};

