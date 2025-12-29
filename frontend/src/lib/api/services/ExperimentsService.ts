/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnalyzeExperimentRequestBody } from '../models/AnalyzeExperimentRequestBody';
import type { AnalyzeExperimentResponseBody } from '../models/AnalyzeExperimentResponseBody';
import type { ExecuteEvaluationRequestBody } from '../models/ExecuteEvaluationRequestBody';
import type { ExecuteEvaluationResponseBody } from '../models/ExecuteEvaluationResponseBody';
import type { ExecuteFullRequestBody } from '../models/ExecuteFullRequestBody';
import type { ExecuteFullResponseBody } from '../models/ExecuteFullResponseBody';
import type { ExecuteTrialRequestBody } from '../models/ExecuteTrialRequestBody';
import type { ExecuteTrialResponseBody } from '../models/ExecuteTrialResponseBody';
import type { FetchExperimentalResultsRequestBody } from '../models/FetchExperimentalResultsRequestBody';
import type { FetchExperimentalResultsResponseBody } from '../models/FetchExperimentalResultsResponseBody';
import type { FetchRunIdsRequestBody } from '../models/FetchRunIdsRequestBody';
import type { FetchRunIdsResponseBody } from '../models/FetchRunIdsResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ExperimentsService {
    /**
     * Fetch Run Ids
     * @param requestBody
     * @returns FetchRunIdsResponseBody Successful Response
     * @throws ApiError
     */
    public static fetchRunIdsAirasV1ExperimentsRunIdsPost(
        requestBody: FetchRunIdsRequestBody,
    ): CancelablePromise<FetchRunIdsResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/experiments/run-ids',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Fetch Experimental Results
     * @param requestBody
     * @returns FetchExperimentalResultsResponseBody Successful Response
     * @throws ApiError
     */
    public static fetchExperimentalResultsAirasV1ExperimentsResultsPost(
        requestBody: FetchExperimentalResultsRequestBody,
    ): CancelablePromise<FetchExperimentalResultsResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/experiments/results',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Execute Trial
     * @param requestBody
     * @returns ExecuteTrialResponseBody Successful Response
     * @throws ApiError
     */
    public static executeTrialAirasV1ExperimentsTestRunsPost(
        requestBody: ExecuteTrialRequestBody,
    ): CancelablePromise<ExecuteTrialResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/experiments/test-runs',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Execute Full
     * @param requestBody
     * @returns ExecuteFullResponseBody Successful Response
     * @throws ApiError
     */
    public static executeFullAirasV1ExperimentsFullRunsPost(
        requestBody: ExecuteFullRequestBody,
    ): CancelablePromise<ExecuteFullResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/experiments/full-runs',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Execute Evaluation
     * @param requestBody
     * @returns ExecuteEvaluationResponseBody Successful Response
     * @throws ApiError
     */
    public static executeEvaluationAirasV1ExperimentsEvaluationsPost(
        requestBody: ExecuteEvaluationRequestBody,
    ): CancelablePromise<ExecuteEvaluationResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/experiments/evaluations',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Analyze Experiment
     * @param requestBody
     * @returns AnalyzeExperimentResponseBody Successful Response
     * @throws ApiError
     */
    public static analyzeExperimentAirasV1ExperimentsAnalysesPost(
        requestBody: AnalyzeExperimentRequestBody,
    ): CancelablePromise<AnalyzeExperimentResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/experiments/analyses',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
