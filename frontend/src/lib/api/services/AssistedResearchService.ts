/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AssistedResearchLinkCreateRequest } from '../models/AssistedResearchLinkCreateRequest';
import type { AssistedResearchLinkListResponse } from '../models/AssistedResearchLinkListResponse';
import type { AssistedResearchLinkResponse } from '../models/AssistedResearchLinkResponse';
import type { AssistedResearchSessionCreateRequest } from '../models/AssistedResearchSessionCreateRequest';
import type { AssistedResearchSessionResponse } from '../models/AssistedResearchSessionResponse';
import type { AssistedResearchStepCreateRequest } from '../models/AssistedResearchStepCreateRequest';
import type { AssistedResearchStepResponse } from '../models/AssistedResearchStepResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AssistedResearchService {
    /**
     * Create Session
     * @param requestBody
     * @returns AssistedResearchSessionResponse Successful Response
     * @throws ApiError
     */
    public static createSessionAirasV1AssistedResearchSessionPost(
        requestBody: AssistedResearchSessionCreateRequest,
    ): CancelablePromise<AssistedResearchSessionResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/assisted_research/session',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Session
     * @param sessionId
     * @returns AssistedResearchSessionResponse Successful Response
     * @throws ApiError
     */
    public static getSessionAirasV1AssistedResearchSessionSessionIdGet(
        sessionId: string,
    ): CancelablePromise<AssistedResearchSessionResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/v1/assisted_research/session/{session_id}',
            path: {
                'session_id': sessionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Step
     * @param requestBody
     * @returns AssistedResearchStepResponse Successful Response
     * @throws ApiError
     */
    public static createStepAirasV1AssistedResearchStepPost(
        requestBody: AssistedResearchStepCreateRequest,
    ): CancelablePromise<AssistedResearchStepResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/assisted_research/step',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Step
     * @param stepId
     * @returns AssistedResearchStepResponse Successful Response
     * @throws ApiError
     */
    public static getStepAirasV1AssistedResearchStepStepIdGet(
        stepId: string,
    ): CancelablePromise<AssistedResearchStepResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/v1/assisted_research/step/{step_id}',
            path: {
                'step_id': stepId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Link
     * @param requestBody
     * @returns AssistedResearchLinkResponse Successful Response
     * @throws ApiError
     */
    public static createLinkAirasV1AssistedResearchLinkPost(
        requestBody: AssistedResearchLinkCreateRequest,
    ): CancelablePromise<AssistedResearchLinkResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/assisted_research/link',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Link
     * @param fromStepId
     * @returns AssistedResearchLinkListResponse Successful Response
     * @throws ApiError
     */
    public static getLinkAirasV1AssistedResearchLinkFromStepIdGet(
        fromStepId: string,
    ): CancelablePromise<AssistedResearchLinkListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/v1/assisted_research/link/{from_step_id}',
            path: {
                'from_step_id': fromStepId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
