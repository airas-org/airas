/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Status } from './Status';
import type { StepType } from './StepType';
export type TopicOpenEndedResearchListItemResponse = {
    id: string;
    title: string;
    created_by: string;
    created_at: string;
    status: Status;
    current_step?: (StepType | null);
    error_message?: (string | null);
    last_updated_at: string;
    github_url?: (string | null);
};

