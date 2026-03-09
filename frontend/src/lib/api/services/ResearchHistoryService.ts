/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GithubDownloadRequest } from '../models/GithubDownloadRequest';
import type { GithubDownloadResponse } from '../models/GithubDownloadResponse';
import type { GithubUploadRequest } from '../models/GithubUploadRequest';
import type { GithubUploadResponse } from '../models/GithubUploadResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ResearchHistoryService {
    /**
     * Download Research History
     * @param requestBody
     * @param xGithubSession
     * @returns GithubDownloadResponse Successful Response
     * @throws ApiError
     */
    public static downloadResearchHistoryAirasV1ResearchHistoryDownloadPost(
        requestBody: GithubDownloadRequest,
        xGithubSession?: (string | null),
    ): CancelablePromise<GithubDownloadResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/research-history/download',
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
     * Upload Research History
     * @param requestBody
     * @param xGithubSession
     * @returns GithubUploadResponse Successful Response
     * @throws ApiError
     */
    public static uploadResearchHistoryAirasV1ResearchHistoryUploadPost(
        requestBody: GithubUploadRequest,
        xGithubSession?: (string | null),
    ): CancelablePromise<GithubUploadResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/research-history/upload',
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
