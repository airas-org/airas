/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RetrieveModelsSubgraphRequestBody } from '../models/RetrieveModelsSubgraphRequestBody';
import type { RetrieveModelsSubgraphResponseBody } from '../models/RetrieveModelsSubgraphResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ModelsService {
    /**
     * Retrieve Models
     * @param requestBody
     * @returns RetrieveModelsSubgraphResponseBody Successful Response
     * @throws ApiError
     */
    public static retrieveModelsAirasV1ModelsGet(
        requestBody: RetrieveModelsSubgraphRequestBody,
    ): CancelablePromise<RetrieveModelsSubgraphResponseBody> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/v1/models',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
