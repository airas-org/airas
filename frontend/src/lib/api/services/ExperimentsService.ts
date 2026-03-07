/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnalyzeExperimentRequestBody } from '../models/AnalyzeExperimentRequestBody';
import type { AnalyzeExperimentResponseBody } from '../models/AnalyzeExperimentResponseBody';
import type { DispatchDiagramGenerationRequestBody } from '../models/DispatchDiagramGenerationRequestBody';
import type { DispatchDiagramGenerationResponseBody } from '../models/DispatchDiagramGenerationResponseBody';
import type { DispatchExperimentValidationRequestBody } from '../models/DispatchExperimentValidationRequestBody';
import type { DispatchExperimentValidationResponseBody } from '../models/DispatchExperimentValidationResponseBody';
import type { DispatchMainExperimentRequestBody } from '../models/DispatchMainExperimentRequestBody';
import type { DispatchMainExperimentResponseBody } from '../models/DispatchMainExperimentResponseBody';
import type { DispatchSanityCheckRequestBody } from '../models/DispatchSanityCheckRequestBody';
import type { DispatchSanityCheckResponseBody } from '../models/DispatchSanityCheckResponseBody';
import type { DispatchVisualizationRequestBody } from '../models/DispatchVisualizationRequestBody';
import type { DispatchVisualizationResponseBody } from '../models/DispatchVisualizationResponseBody';
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
     * @param xGithubSession
     * @returns FetchRunIdsResponseBody Successful Response
     * @throws ApiError
     */
    public static fetchRunIdsAirasV1ExperimentsRunIdsPost(
        requestBody: FetchRunIdsRequestBody,
        xGithubSession?: (string | null),
    ): CancelablePromise<FetchRunIdsResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/experiments/run-ids',
            headers: {
                'x-github-session': xGithubSession,
            },
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
     * @param xGithubSession
     * @returns FetchExperimentalResultsResponseBody Successful Response
     * @throws ApiError
     */
    public static fetchExperimentalResultsAirasV1ExperimentsResultsPost(
        requestBody: FetchExperimentalResultsRequestBody,
        xGithubSession?: (string | null),
    ): CancelablePromise<FetchExperimentalResultsResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/experiments/results',
            headers: {
                'x-github-session': xGithubSession,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Dispatch Sanity Check
     * @param requestBody
     * @param xGithubSession
     * @returns DispatchSanityCheckResponseBody Successful Response
     * @throws ApiError
     */
    public static dispatchSanityCheckAirasV1ExperimentsSanityChecksDispatchPost(
        requestBody: DispatchSanityCheckRequestBody,
        xGithubSession?: (string | null),
    ): CancelablePromise<DispatchSanityCheckResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/experiments/sanity-checks/dispatch',
            headers: {
                'x-github-session': xGithubSession,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Dispatch Experiment Validation
     * @param requestBody
     * @param xGithubSession
     * @returns DispatchExperimentValidationResponseBody Successful Response
     * @throws ApiError
     */
    public static dispatchExperimentValidationAirasV1ExperimentsValidationsDispatchPost(
        requestBody: DispatchExperimentValidationRequestBody,
        xGithubSession?: (string | null),
    ): CancelablePromise<DispatchExperimentValidationResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/experiments/validations/dispatch',
            headers: {
                'x-github-session': xGithubSession,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Dispatch Main Experiment
     * @param requestBody
     * @param xGithubSession
     * @returns DispatchMainExperimentResponseBody Successful Response
     * @throws ApiError
     */
    public static dispatchMainExperimentAirasV1ExperimentsMainRunsDispatchPost(
        requestBody: DispatchMainExperimentRequestBody,
        xGithubSession?: (string | null),
    ): CancelablePromise<DispatchMainExperimentResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/experiments/main-runs/dispatch',
            headers: {
                'x-github-session': xGithubSession,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Dispatch Visualization
     * @param requestBody
     * @param xGithubSession
     * @returns DispatchVisualizationResponseBody Successful Response
     * @throws ApiError
     */
    public static dispatchVisualizationAirasV1ExperimentsVisualizationsDispatchPost(
        requestBody: DispatchVisualizationRequestBody,
        xGithubSession?: (string | null),
    ): CancelablePromise<DispatchVisualizationResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/experiments/visualizations/dispatch',
            headers: {
                'x-github-session': xGithubSession,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Dispatch Diagram Generation
     * @param requestBody
     * @param xGithubSession
     * @returns DispatchDiagramGenerationResponseBody Successful Response
     * @throws ApiError
     */
    public static dispatchDiagramGenerationAirasV1ExperimentsDiagramsDispatchPost(
        requestBody: DispatchDiagramGenerationRequestBody,
        xGithubSession?: (string | null),
    ): CancelablePromise<DispatchDiagramGenerationResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/experiments/diagrams/dispatch',
            headers: {
                'x-github-session': xGithubSession,
            },
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
