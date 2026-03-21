/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApiKeyListResponse } from '../models/ApiKeyListResponse';
import type { ApiKeyResponse } from '../models/ApiKeyResponse';
import type { ApiProvider } from '../models/ApiProvider';
import type { SaveApiKeyRequest } from '../models/SaveApiKeyRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class EeApiKeysService {
    /**
     * List Api Keys
     * @returns ApiKeyListResponse Successful Response
     * @throws ApiError
     */
    public static listApiKeysAirasEeApiKeysGet(): CancelablePromise<ApiKeyListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/ee/api-keys',
        });
    }
    /**
     * Save Api Key
     * @param requestBody
     * @returns ApiKeyResponse Successful Response
     * @throws ApiError
     */
    public static saveApiKeyAirasEeApiKeysPost(
        requestBody: SaveApiKeyRequest,
    ): CancelablePromise<ApiKeyResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/ee/api-keys',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Api Key
     * @param provider
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteApiKeyAirasEeApiKeysProviderDelete(
        provider: ApiProvider,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/airas/ee/api-keys/{provider}',
            path: {
                'provider': provider,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
