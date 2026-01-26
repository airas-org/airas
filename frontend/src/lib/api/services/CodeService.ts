/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GenerateCodeSubgraphRequestBody } from '../models/GenerateCodeSubgraphRequestBody';
import type { GenerateCodeSubgraphResponseBody } from '../models/GenerateCodeSubgraphResponseBody';
import type { PushCodeSubgraphRequestBody } from '../models/PushCodeSubgraphRequestBody';
import type { PushCodeSubgraphResponseBody } from '../models/PushCodeSubgraphResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CodeService {
    /**
     * Generate Code
     * @param requestBody
     * @returns GenerateCodeSubgraphResponseBody Successful Response
     * @throws ApiError
     */
    public static generateCodeAirasV1CodeGenerationsPost(
        requestBody: GenerateCodeSubgraphRequestBody,
    ): CancelablePromise<GenerateCodeSubgraphResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/code/generations',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Push Code
     * @param requestBody
     * @returns PushCodeSubgraphResponseBody Successful Response
     * @throws ApiError
     */
    public static pushCodeAirasV1CodePushPost(
        requestBody: PushCodeSubgraphRequestBody,
    ): CancelablePromise<PushCodeSubgraphResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/code/push',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
