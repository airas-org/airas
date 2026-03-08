/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GitHubAuthorizeResponse } from '../models/GitHubAuthorizeResponse';
import type { GitHubCallbackRequest } from '../models/GitHubCallbackRequest';
import type { GitHubConnectionStatus } from '../models/GitHubConnectionStatus';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class EeGithubOauthService {
    /**
     * Authorize
     * @param redirectUri
     * @returns GitHubAuthorizeResponse Successful Response
     * @throws ApiError
     */
    public static authorizeAirasEeGithubAuthorizeGet(
        redirectUri: string,
    ): CancelablePromise<GitHubAuthorizeResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/ee/github/authorize',
            query: {
                'redirect_uri': redirectUri,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Callback
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static callbackAirasEeGithubCallbackPost(
        requestBody: GitHubCallbackRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/ee/github/callback',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Status
     * @param xGithubSession
     * @returns GitHubConnectionStatus Successful Response
     * @throws ApiError
     */
    public static statusAirasEeGithubStatusGet(
        xGithubSession?: (string | null),
    ): CancelablePromise<GitHubConnectionStatus> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/ee/github/status',
            headers: {
                'x-github-session': xGithubSession,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Disconnect
     * @param xGithubSession
     * @returns any Successful Response
     * @throws ApiError
     */
    public static disconnectAirasEeGithubDisconnectDelete(
        xGithubSession?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/airas/ee/github/disconnect',
            headers: {
                'x-github-session': xGithubSession,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
