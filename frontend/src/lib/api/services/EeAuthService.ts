/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GetMeResponse } from '../models/GetMeResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class EeAuthService {
    /**
     * Get Me
     * Return the current authenticated user's ID.
     * @returns GetMeResponse Successful Response
     * @throws ApiError
     */
    public static getMeAirasEeAuthMeGet(): CancelablePromise<GetMeResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/ee/auth/me',
        });
    }
}
