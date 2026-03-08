/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { UserPlanResponse } from '../models/UserPlanResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class EePlanService {
    /**
     * Get Plan
     * @returns UserPlanResponse Successful Response
     * @throws ApiError
     */
    public static getPlanAirasEePlanGet(): CancelablePromise<UserPlanResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/ee/plan',
        });
    }
}
