/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ListCredentialsResponseBody } from '../models/ListCredentialsResponseBody';
import type { UpdateCredentialsRequestBody } from '../models/UpdateCredentialsRequestBody';
import type { UpdateCredentialsResponseBody } from '../models/UpdateCredentialsResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CredentialsService {
    /**
     * List Credentials
     * Report which credentials are configured (values are never returned in full for secrets).
     * @returns ListCredentialsResponseBody Successful Response
     * @throws ApiError
     */
    public static listCredentialsAirasV1CredentialsGet(): CancelablePromise<ListCredentialsResponseBody> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/v1/credentials',
        });
    }
    /**
     * Update Credentials
     * Merge credential updates into ~/.airas/credentials.json.
     *
     * An empty-string value removes the credential. Only known credential
     * names are accepted.
     * @param requestBody
     * @returns UpdateCredentialsResponseBody Successful Response
     * @throws ApiError
     */
    public static updateCredentialsAirasV1CredentialsPut(
        requestBody: UpdateCredentialsRequestBody,
    ): CancelablePromise<UpdateCredentialsResponseBody> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/airas/v1/credentials',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
