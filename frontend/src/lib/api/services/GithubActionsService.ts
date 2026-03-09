/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DownloadGithubActionsArtifactsRequestBody } from '../models/DownloadGithubActionsArtifactsRequestBody';
import type { DownloadGithubActionsArtifactsResponseBody } from '../models/DownloadGithubActionsArtifactsResponseBody';
import type { PollGithubActionsRequestBody } from '../models/PollGithubActionsRequestBody';
import type { PollGithubActionsResponseBody } from '../models/PollGithubActionsResponseBody';
import type { SetGithubActionsSecretsRequestBody } from '../models/SetGithubActionsSecretsRequestBody';
import type { SetGithubActionsSecretsResponseBody } from '../models/SetGithubActionsSecretsResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class GithubActionsService {
    /**
     * Poll Github Actions
     * @param requestBody
     * @param xGithubSession
     * @returns PollGithubActionsResponseBody Successful Response
     * @throws ApiError
     */
    public static pollGithubActionsAirasV1GithubActionsPollingPost(
        requestBody: PollGithubActionsRequestBody,
        xGithubSession?: (string | null),
    ): CancelablePromise<PollGithubActionsResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/github-actions/polling',
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
     * Set Github Actions Secrets
     * @param requestBody
     * @param xGithubSession
     * @returns SetGithubActionsSecretsResponseBody Successful Response
     * @throws ApiError
     */
    public static setGithubActionsSecretsAirasV1GithubActionsSecretsPost(
        requestBody: SetGithubActionsSecretsRequestBody,
        xGithubSession?: (string | null),
    ): CancelablePromise<SetGithubActionsSecretsResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/github-actions/secrets',
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
     * Download Github Actions Artifacts
     * @param requestBody
     * @param xGithubSession
     * @returns DownloadGithubActionsArtifactsResponseBody Successful Response
     * @throws ApiError
     */
    public static downloadGithubActionsArtifactsAirasV1GithubActionsArtifactsDownloadPost(
        requestBody: DownloadGithubActionsArtifactsRequestBody,
        xGithubSession?: (string | null),
    ): CancelablePromise<DownloadGithubActionsArtifactsResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/github-actions/artifacts/download',
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
}
