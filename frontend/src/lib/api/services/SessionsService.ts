/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import type { SessionCreateRequest } from "../models/SessionCreateRequest";
import type { SessionResponse } from "../models/SessionResponse";
export class SessionsService {
  /**
   * Create Session
   * @param requestBody
   * @returns SessionResponse Successful Response
   * @throws ApiError
   */
  public static createSessionAirasV1SessionsPost(
    requestBody: SessionCreateRequest,
  ): CancelablePromise<SessionResponse> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/airas/v1/sessions",
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get Session
   * @param sessionId
   * @returns SessionResponse Successful Response
   * @throws ApiError
   */
  public static getSessionAirasV1SessionsSessionIdGet(
    sessionId: string,
  ): CancelablePromise<SessionResponse> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/airas/v1/sessions/{session_id}",
      path: {
        session_id: sessionId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
}
