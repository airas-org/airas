/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CompileLatexSubgraphRequestBody } from '../models/CompileLatexSubgraphRequestBody';
import type { CompileLatexSubgraphResponseBody } from '../models/CompileLatexSubgraphResponseBody';
import type { GenerateLatexSubgraphRequestBody } from '../models/GenerateLatexSubgraphRequestBody';
import type { GenerateLatexSubgraphResponseBody } from '../models/GenerateLatexSubgraphResponseBody';
import type { PushLatexSubgraphRequestBody } from '../models/PushLatexSubgraphRequestBody';
import type { PushLatexSubgraphResponseBody } from '../models/PushLatexSubgraphResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class LatexService {
    /**
     * Generate Latex
     * @param requestBody
     * @returns GenerateLatexSubgraphResponseBody Successful Response
     * @throws ApiError
     */
    public static generateLatexAirasV1LatexGenerationsPost(
        requestBody: GenerateLatexSubgraphRequestBody,
    ): CancelablePromise<GenerateLatexSubgraphResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/latex/generations',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Push Latex
     * @param requestBody
     * @returns PushLatexSubgraphResponseBody Successful Response
     * @throws ApiError
     */
    public static pushLatexAirasV1LatexPushPost(
        requestBody: PushLatexSubgraphRequestBody,
    ): CancelablePromise<PushLatexSubgraphResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/latex/push',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Compile Latex
     * @param requestBody
     * @returns CompileLatexSubgraphResponseBody Successful Response
     * @throws ApiError
     */
    public static compileLatexAirasV1LatexCompilePost(
        requestBody: CompileLatexSubgraphRequestBody,
    ): CancelablePromise<CompileLatexSubgraphResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/latex/compile',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
