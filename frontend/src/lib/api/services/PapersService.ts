/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import type { RetrievePaperSubgraphRequestBody } from "../models/RetrievePaperSubgraphRequestBody";
import type { RetrievePaperSubgraphResponseBody } from "../models/RetrievePaperSubgraphResponseBody";
import type { WriteSubgraphRequestBody } from "../models/WriteSubgraphRequestBody";
import type { WriteSubgraphResponseBody } from "../models/WriteSubgraphResponseBody";
export class PapersService {
  /**
   * Get Paper Title
   * @param requestBody
   * @returns RetrievePaperSubgraphResponseBody Successful Response
   * @throws ApiError
   */
  public static getPaperTitleAirasV1PapersPost(
    requestBody: RetrievePaperSubgraphRequestBody,
  ): CancelablePromise<RetrievePaperSubgraphResponseBody> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/airas/v1/papers",
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Generate Paper
   * @param requestBody
   * @returns WriteSubgraphResponseBody Successful Response
   * @throws ApiError
   */
  public static generatePaperAirasV1PapersGenerationsPost(
    requestBody: WriteSubgraphRequestBody,
  ): CancelablePromise<WriteSubgraphResponseBody> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/airas/v1/papers/generations",
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
}
