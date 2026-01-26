/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Status } from './Status';
import type { StepType } from './StepType';
export type AssistedResearchStepResponse = {
    id: string;
    session_id: string;
    created_by: string;
    created_at: string;
    status: Status;
    step_type: StepType;
    error_message: (string | null);
    result: any;
    schema_version: number;
};

