/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TopicOpenEndedResearchListResponseBody } from '../models/TopicOpenEndedResearchListResponseBody';
import type { TopicOpenEndedResearchRequestBody } from '../models/TopicOpenEndedResearchRequestBody';
import type { TopicOpenEndedResearchResponseBody } from '../models/TopicOpenEndedResearchResponseBody';
import type { TopicOpenEndedResearchStatusResponseBody } from '../models/TopicOpenEndedResearchStatusResponseBody';
import type { TopicOpenEndedResearchUpdateRequestBody } from '../models/TopicOpenEndedResearchUpdateRequestBody';
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
    public static executeTopicOpenEndedResearchAirasV1TopicOpenEndedResearchRunPost(
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
    public static getTopicOpenEndedResearchStatusAirasV1TopicOpenEndedResearchStatusTaskIdGet(
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
    /**
     * List Topic Open Ended Research
     * @param offset
     * @param limit
     * @returns TopicOpenEndedResearchListResponseBody Successful Response
     * @throws ApiError
     */
    public static listTopicOpenEndedResearchAirasV1TopicOpenEndedResearchGet(
        offset?: number,
        limit?: (number | null),
    ): CancelablePromise<TopicOpenEndedResearchListResponseBody> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/v1/topic_open_ended_research',
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
     * Update Topic Open Ended Research
     * @param taskId
     * @param requestBody
     * @returns TopicOpenEndedResearchStatusResponseBody Successful Response
     * @throws ApiError
     */
    public static updateTopicOpenEndedResearchAirasV1TopicOpenEndedResearchTaskIdPatch(
        taskId: string,
        requestBody: TopicOpenEndedResearchUpdateRequestBody,
    ): CancelablePromise<TopicOpenEndedResearchStatusResponseBody> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/airas/v1/topic_open_ended_research/{task_id}',
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
