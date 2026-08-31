/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DispatchPaperReproductionGenerateRequestBody } from '../models/DispatchPaperReproductionGenerateRequestBody';
import type { DispatchPaperReproductionGenerateResponseBody } from '../models/DispatchPaperReproductionGenerateResponseBody';
import type { DispatchPaperReproductionRunRequestBody } from '../models/DispatchPaperReproductionRunRequestBody';
import type { DispatchPaperReproductionRunResponseBody } from '../models/DispatchPaperReproductionRunResponseBody';
import type { DispatchParameterTuningRunRequestBody } from '../models/DispatchParameterTuningRunRequestBody';
import type { DispatchParameterTuningRunResponseBody } from '../models/DispatchParameterTuningRunResponseBody';
import type { FetchPaperReproductionResultsRequestBody } from '../models/FetchPaperReproductionResultsRequestBody';
import type { FetchPaperReproductionResultsResponseBody } from '../models/FetchPaperReproductionResultsResponseBody';
import type { FetchParameterTuningResultsRequestBody } from '../models/FetchParameterTuningResultsRequestBody';
import type { FetchParameterTuningResultsResponseBody } from '../models/FetchParameterTuningResultsResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class PaperReproductionService {
    /**
     * Dispatch Paper Reproduction Generate
     * @param requestBody
     * @returns DispatchPaperReproductionGenerateResponseBody Successful Response
     * @throws ApiError
     */
    public static dispatchPaperReproductionGenerateAirasV1PaperReproductionGenerateDispatchPost(
        requestBody: DispatchPaperReproductionGenerateRequestBody,
    ): CancelablePromise<DispatchPaperReproductionGenerateResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/paper-reproduction/generate/dispatch',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Dispatch Paper Reproduction Run
     * @param requestBody
     * @returns DispatchPaperReproductionRunResponseBody Successful Response
     * @throws ApiError
     */
    public static dispatchPaperReproductionRunAirasV1PaperReproductionRunDispatchPost(
        requestBody: DispatchPaperReproductionRunRequestBody,
    ): CancelablePromise<DispatchPaperReproductionRunResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/paper-reproduction/run/dispatch',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Fetch Paper Reproduction Results
     * @param requestBody
     * @returns FetchPaperReproductionResultsResponseBody Successful Response
     * @throws ApiError
     */
    public static fetchPaperReproductionResultsAirasV1PaperReproductionResultsPost(
        requestBody: FetchPaperReproductionResultsRequestBody,
    ): CancelablePromise<FetchPaperReproductionResultsResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/paper-reproduction/results',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Dispatch Parameter Tuning Run
     * @param requestBody
     * @returns DispatchParameterTuningRunResponseBody Successful Response
     * @throws ApiError
     */
    public static dispatchParameterTuningRunAirasV1PaperReproductionParameterTuningDispatchPost(
        requestBody: DispatchParameterTuningRunRequestBody,
    ): CancelablePromise<DispatchParameterTuningRunResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/paper-reproduction/parameter-tuning/dispatch',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Fetch Parameter Tuning Results
     * @param requestBody
     * @returns FetchParameterTuningResultsResponseBody Successful Response
     * @throws ApiError
     */
    public static fetchParameterTuningResultsAirasV1PaperReproductionParameterTuningResultsPost(
        requestBody: FetchParameterTuningResultsRequestBody,
    ): CancelablePromise<FetchParameterTuningResultsResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/paper-reproduction/parameter-tuning/results',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
