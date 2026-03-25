/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GitHubAuthorizeResponse } from '../models/GitHubAuthorizeResponse';
import type { GitHubCallbackRequest } from '../models/GitHubCallbackRequest';
import type { GitHubCallbackResponse } from '../models/GitHubCallbackResponse';
import type { GitHubConnectionStatus } from '../models/GitHubConnectionStatus';
import type { GitHubDisconnectResponse } from '../models/GitHubDisconnectResponse';
import type { GitHubProxyCompleteRequest } from '../models/GitHubProxyCompleteRequest';
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
     * @returns GitHubCallbackResponse Successful Response
     * @throws ApiError
     */
    public static callbackAirasEeGithubCallbackPost(
        requestBody: GitHubCallbackRequest,
    ): CancelablePromise<GitHubCallbackResponse> {
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
     * @returns GitHubDisconnectResponse Successful Response
     * @throws ApiError
     */
    public static disconnectAirasEeGithubDisconnectDelete(
        xGithubSession?: (string | null),
    ): CancelablePromise<GitHubDisconnectResponse> {
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
    /**
     * Proxy Authorize
     * Return a GitHub authorize URL for the OAuth Proxy flow.
     *
     * Called by preview frontends.  The ``origin`` is embedded in the state
     * so that the proxy-callback can redirect back to the correct frontend.
     * @param origin
     * @returns GitHubAuthorizeResponse Successful Response
     * @throws ApiError
     */
    public static proxyAuthorizeAirasEeGithubProxyAuthorizeGet(
        origin: string,
    ): CancelablePromise<GitHubAuthorizeResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/ee/github/proxy-authorize',
            query: {
                'origin': origin,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Proxy Callback
     * Receive the OAuth callback from GitHub and redirect to the preview frontend.
     *
     * This endpoint runs on the production/develop backend (the fixed callback URL
     * registered with the GitHub App).  It exchanges the code for credentials,
     * wraps them in a short-lived JWT, and 302-redirects to the preview frontend.
     * @param code
     * @param state
     * @returns any Successful Response
     * @throws ApiError
     */
    public static proxyCallbackAirasEeGithubProxyCallbackGet(
        code: string,
        state: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/ee/github/proxy-callback',
            query: {
                'code': code,
                'state': state,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Proxy Complete
     * Complete the OAuth Proxy flow on the preview backend.
     *
     * The preview frontend sends the proxy JWT it received via redirect.
     * This endpoint validates the JWT, creates a local session, and stores
     * the GitHub token in this environment's own database.
     * @param requestBody
     * @returns GitHubCallbackResponse Successful Response
     * @throws ApiError
     */
    public static proxyCompleteAirasEeGithubProxyCompletePost(
        requestBody: GitHubProxyCompleteRequest,
    ): CancelablePromise<GitHubCallbackResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/ee/github/proxy-complete',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
