/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PrepareRepositorySubgraphRequestBody } from '../models/PrepareRepositorySubgraphRequestBody';
import type { PrepareRepositorySubgraphResponseBody } from '../models/PrepareRepositorySubgraphResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class RepositoriesService {
    /**
     * Prepare Repository
     * @param requestBody
     * @returns PrepareRepositorySubgraphResponseBody Successful Response
     * @throws ApiError
     */
    public static prepareRepositoryAirasV1RepositoriesPost(
        requestBody: PrepareRepositorySubgraphRequestBody,
    ): CancelablePromise<PrepareRepositorySubgraphResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/repositories',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
