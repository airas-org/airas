/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TopicOpenEndedResearchRequestBody } from '../models/TopicOpenEndedResearchRequestBody';
import type { TopicOpenEndedResearchResponseBody } from '../models/TopicOpenEndedResearchResponseBody';
import type { TopicOpenEndedResearchStatusResponseBody } from '../models/TopicOpenEndedResearchStatusResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class TopicOpenEndedResearchService {
    /**
     * Execute Topic Open Ended Research
     * @param requestBody
     * @returns TopicOpenEndedResearchResponseBody Successful Response
     * @throws ApiError
     */
    public static run(
        requestBody: TopicOpenEndedResearchRequestBody,
    ): CancelablePromise<TopicOpenEndedResearchResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/topic_open_ended_research/run',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Topic Open Ended Research Status
     * @param taskId
     * @returns TopicOpenEndedResearchStatusResponseBody Successful Response
     * @throws ApiError
     */
    public static getStatus(
        taskId: string,
    ): CancelablePromise<TopicOpenEndedResearchStatusResponseBody> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/v1/topic_open_ended_research/status/{task_id}',
            path: {
                'task_id': taskId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
