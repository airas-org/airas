/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelInteractiveRepoAgentRequestBody } from '../models/CancelInteractiveRepoAgentRequestBody';
import type { CancelInteractiveRepoAgentResponseBody } from '../models/CancelInteractiveRepoAgentResponseBody';
import type { DispatchInteractiveRepoAgentRequestBody } from '../models/DispatchInteractiveRepoAgentRequestBody';
import type { DispatchInteractiveRepoAgentResponseBody } from '../models/DispatchInteractiveRepoAgentResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class InteractiveRepoAgentService {
    /**
     * Dispatch Interactive Repo Agent
     * @param requestBody
     * @returns DispatchInteractiveRepoAgentResponseBody Successful Response
     * @throws ApiError
     */
    public static dispatchInteractiveRepoAgentAirasV1InteractiveRepoAgentDispatchPost(
        requestBody: DispatchInteractiveRepoAgentRequestBody,
    ): CancelablePromise<DispatchInteractiveRepoAgentResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/interactive-repo-agent/dispatch',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Cancel Interactive Repo Agent
     * @param workflowRunId
     * @param requestBody
     * @returns CancelInteractiveRepoAgentResponseBody Successful Response
     * @throws ApiError
     */
    public static cancelInteractiveRepoAgentAirasV1InteractiveRepoAgentWorkflowRunIdCancelPost(
        workflowRunId: number,
        requestBody: CancelInteractiveRepoAgentRequestBody,
    ): CancelablePromise<CancelInteractiveRepoAgentResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/interactive-repo-agent/{workflow_run_id}/cancel',
            path: {
                'workflow_run_id': workflowRunId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
