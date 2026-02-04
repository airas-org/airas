/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
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
     * @returns PollGithubActionsResponseBody Successful Response
     * @throws ApiError
     */
    public static pollGithubActionsAirasV1GithubActionsPollingPost(
        requestBody: PollGithubActionsRequestBody,
    ): CancelablePromise<PollGithubActionsResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/github-actions/polling',
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
     * @returns SetGithubActionsSecretsResponseBody Successful Response
     * @throws ApiError
     */
    public static setGithubActionsSecretsAirasV1GithubActionsSecretsPost(
        requestBody: SetGithubActionsSecretsRequestBody,
    ): CancelablePromise<SetGithubActionsSecretsResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/github-actions/secrets',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
