/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GenerateHypothesisSubgraphV0RequestBody } from '../models/GenerateHypothesisSubgraphV0RequestBody';
import type { GenerateHypothesisSubgraphV0ResponseBody } from '../models/GenerateHypothesisSubgraphV0ResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class HypothesesService {
    /**
     * Generate Hypotheses
     * @param requestBody
     * @returns GenerateHypothesisSubgraphV0ResponseBody Successful Response
     * @throws ApiError
     */
    public static generateHypothesesAirasV1HypothesesGenerationsPost(
        requestBody: GenerateHypothesisSubgraphV0RequestBody,
    ): CancelablePromise<GenerateHypothesisSubgraphV0ResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/hypotheses/generations',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
