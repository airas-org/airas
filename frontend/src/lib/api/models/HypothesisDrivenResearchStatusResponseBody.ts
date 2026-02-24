/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ResearchHistory_Output } from './ResearchHistory_Output';
import type { Status } from './Status';
import type { StepType } from './StepType';
export type HypothesisDrivenResearchStatusResponseBody = {
    id: string;
    title: string;
    created_by: string;
    created_at: string;
    status: Status;
    current_step?: (StepType | null);
    error_message?: (string | null);
    last_updated_at: string;
    result: Record<string, any>;
    github_url?: (string | null);
    readonly task_id: string;
    readonly error: (string | null);
    readonly research_history: (ResearchHistory_Output | null);
};

