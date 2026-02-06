/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PushGitHubRequestBody } from '../models/PushGitHubRequestBody';
import type { PushGitHubResponseBody } from '../models/PushGitHubResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class GithubService {
    /**
     * Push Github
     * @param requestBody
     * @returns PushGitHubResponseBody Successful Response
     * @throws ApiError
     */
    public static pushGithubAirasV1GithubPushPost(
        requestBody: PushGitHubRequestBody,
    ): CancelablePromise<PushGitHubResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/github/push',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
