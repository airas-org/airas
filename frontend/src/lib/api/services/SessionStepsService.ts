/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import type { SessionStepCreateRequest } from "../models/SessionStepCreateRequest";
import type { SessionStepResponse } from "../models/SessionStepResponse";
export class SessionStepsService {
  /**
   * Create Session Step
   * @param requestBody
   * @returns SessionStepResponse Successful Response
   * @throws ApiError
   */
  public static createSessionStepAirasV1SessionStepsPost(
    requestBody: SessionStepCreateRequest,
  ): CancelablePromise<SessionStepResponse> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/airas/v1/session-steps",
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get Session Step
   * @param stepId
   * @returns SessionStepResponse Successful Response
   * @throws ApiError
   */
  public static getSessionStepAirasV1SessionStepsStepIdGet(
    stepId: string,
  ): CancelablePromise<SessionStepResponse> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/airas/v1/session-steps/{step_id}",
      path: {
        step_id: stepId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
}
