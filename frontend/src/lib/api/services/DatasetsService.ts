/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import type { RetrieveDatasetsSubgraphRequestBody } from "../models/RetrieveDatasetsSubgraphRequestBody";
import type { RetrieveDatasetsSubgraphResponseBody } from "../models/RetrieveDatasetsSubgraphResponseBody";
export class DatasetsService {
  /**
   * Retrieve Datasets
   * @param requestBody
   * @returns RetrieveDatasetsSubgraphResponseBody Successful Response
   * @throws ApiError
   */
  public static retrieveDatasetsAirasV1DatasetsPost(
    requestBody: RetrieveDatasetsSubgraphRequestBody,
  ): CancelablePromise<RetrieveDatasetsSubgraphResponseBody> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/airas/v1/datasets",
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
}
