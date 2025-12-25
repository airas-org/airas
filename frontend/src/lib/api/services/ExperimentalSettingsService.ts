/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GenerateExperimentalDesignSubgraphRequestBody } from '../models/GenerateExperimentalDesignSubgraphRequestBody';
import type { GenerateExperimentalDesignSubgraphResponseBody } from '../models/GenerateExperimentalDesignSubgraphResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ExperimentalSettingsService {
    /**
     * Generate Experimental Design
     * @param requestBody
     * @returns GenerateExperimentalDesignSubgraphResponseBody Successful Response
     * @throws ApiError
     */
    public static generateExperimentalDesignAirasV1ExperimentalSettingsGenerationsPost(
        requestBody: GenerateExperimentalDesignSubgraphRequestBody,
    ): CancelablePromise<GenerateExperimentalDesignSubgraphResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/experimental_settings/generations',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
