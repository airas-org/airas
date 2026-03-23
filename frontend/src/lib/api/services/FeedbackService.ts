/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CreateFeedbackRequestBody } from '../models/CreateFeedbackRequestBody';
import type { CreateFeedbackResponseBody } from '../models/CreateFeedbackResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class FeedbackService {
    /**
     * Create Feedback
     * @param requestBody
     * @returns CreateFeedbackResponseBody Successful Response
     * @throws ApiError
     */
    public static createFeedbackAirasV1FeedbackPost(
        requestBody: CreateFeedbackRequestBody,
    ): CancelablePromise<CreateFeedbackResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/feedback',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
