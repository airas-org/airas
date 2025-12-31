/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import type { ExecuteE2ERequestBody } from "../models/ExecuteE2ERequestBody";
import type { ExecuteE2EResponseBody } from "../models/ExecuteE2EResponseBody";
export class E2EService {
  /**
   * Execute E2E
   * @param requestBody
   * @returns ExecuteE2EResponseBody Successful Response
   * @throws ApiError
   */
  public static executeE2EAirasV1E2ERunPost(
    requestBody: ExecuteE2ERequestBody,
  ): CancelablePromise<ExecuteE2EResponseBody> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/airas/v1/e2e/run",
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get E2E Status
   * @param taskId
   * @returns ExecuteE2EResponseBody Successful Response
   * @throws ApiError
   */
  public static getE2EStatusAirasV1E2EStatusTaskIdGet(
    taskId: string,
  ): CancelablePromise<ExecuteE2EResponseBody> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/airas/v1/e2e/status/{task_id}",
      path: {
        task_id: taskId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
}
