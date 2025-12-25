/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { StepRunLinkCreateRequest } from '../models/StepRunLinkCreateRequest';
import type { StepRunLinkListResponse } from '../models/StepRunLinkListResponse';
import type { StepRunLinkResponse } from '../models/StepRunLinkResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class StepRunLinksService {
    /**
     * Create Step Run Link
     * @param requestBody
     * @returns StepRunLinkResponse Successful Response
     * @throws ApiError
     */
    public static createStepRunLinkAirasV1StepRunLinksPost(
        requestBody: StepRunLinkCreateRequest,
    ): CancelablePromise<StepRunLinkResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/step-run-links',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Step Run Links By From Step Run Id
     * @param fromStepRunId
     * @returns StepRunLinkListResponse Successful Response
     * @throws ApiError
     */
    public static listStepRunLinksByFromStepRunIdAirasV1StepRunLinksFromStepRunIdGet(
        fromStepRunId: string,
    ): CancelablePromise<StepRunLinkListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/v1/step-run-links/{from_step_run_id}',
            path: {
                'from_step_run_id': fromStepRunId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
