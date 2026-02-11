/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DispatchCodeGenerationRequestBody } from '../models/DispatchCodeGenerationRequestBody';
import type { DispatchCodeGenerationResponseBody } from '../models/DispatchCodeGenerationResponseBody';
import type { FetchExperimentCodeRequestBody } from '../models/FetchExperimentCodeRequestBody';
import type { FetchExperimentCodeResponseBody } from '../models/FetchExperimentCodeResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CodeService {
    /**
     * Dispatch Code Generation
     * @param requestBody
     * @returns DispatchCodeGenerationResponseBody Successful Response
     * @throws ApiError
     */
    public static dispatchCodeGenerationAirasV1CodeGenerationsDispatchPost(
        requestBody: DispatchCodeGenerationRequestBody,
    ): CancelablePromise<DispatchCodeGenerationResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/code/generations/dispatch',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Fetch Experiment Code
     * @param requestBody
     * @returns FetchExperimentCodeResponseBody Successful Response
     * @throws ApiError
     */
    public static fetchExperimentCodeAirasV1CodeFetchPost(
        requestBody: FetchExperimentCodeRequestBody,
    ): CancelablePromise<FetchExperimentCodeResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/code/fetch',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
