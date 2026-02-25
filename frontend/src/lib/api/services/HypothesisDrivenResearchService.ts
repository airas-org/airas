/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { HypothesisDrivenResearchListResponseBody } from '../models/HypothesisDrivenResearchListResponseBody';
import type { HypothesisDrivenResearchRequestBody } from '../models/HypothesisDrivenResearchRequestBody';
import type { HypothesisDrivenResearchResponseBody } from '../models/HypothesisDrivenResearchResponseBody';
import type { HypothesisDrivenResearchStatusResponseBody } from '../models/HypothesisDrivenResearchStatusResponseBody';
import type { HypothesisDrivenResearchUpdateRequestBody } from '../models/HypothesisDrivenResearchUpdateRequestBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class HypothesisDrivenResearchService {
    /**
     * Execute Hypothesis Driven Research
     * @param requestBody
     * @returns HypothesisDrivenResearchResponseBody Successful Response
     * @throws ApiError
     */
    public static executeHypothesisDrivenResearchAirasV1HypothesisDrivenResearchRunPost(
        requestBody: HypothesisDrivenResearchRequestBody,
    ): CancelablePromise<HypothesisDrivenResearchResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/hypothesis_driven_research/run',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Hypothesis Driven Research Status
     * @param taskId
     * @returns HypothesisDrivenResearchStatusResponseBody Successful Response
     * @throws ApiError
     */
    public static getHypothesisDrivenResearchStatusAirasV1HypothesisDrivenResearchStatusTaskIdGet(
        taskId: string,
    ): CancelablePromise<HypothesisDrivenResearchStatusResponseBody> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/v1/hypothesis_driven_research/status/{task_id}',
            path: {
                'task_id': taskId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Hypothesis Driven Research
     * @param offset
     * @param limit
     * @returns HypothesisDrivenResearchListResponseBody Successful Response
     * @throws ApiError
     */
    public static listHypothesisDrivenResearchAirasV1HypothesisDrivenResearchGet(
        offset?: number,
        limit?: (number | null),
    ): CancelablePromise<HypothesisDrivenResearchListResponseBody> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/v1/hypothesis_driven_research',
            query: {
                'offset': offset,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Hypothesis Driven Research
     * @param taskId
     * @param requestBody
     * @returns HypothesisDrivenResearchStatusResponseBody Successful Response
     * @throws ApiError
     */
    public static updateHypothesisDrivenResearchAirasV1HypothesisDrivenResearchTaskIdPatch(
        taskId: string,
        requestBody: HypothesisDrivenResearchUpdateRequestBody,
    ): CancelablePromise<HypothesisDrivenResearchStatusResponseBody> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/airas/v1/hypothesis_driven_research/{task_id}',
            path: {
                'task_id': taskId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
