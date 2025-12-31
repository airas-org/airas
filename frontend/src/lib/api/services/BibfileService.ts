/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CancelablePromise } from "../core/CancelablePromise";
import { OpenAPI } from "../core/OpenAPI";
import { request as __request } from "../core/request";
import type { GenerateBibfileSubgraphRequestBody } from "../models/GenerateBibfileSubgraphRequestBody";
import type { GenerateBibfileSubgraphResponseBody } from "../models/GenerateBibfileSubgraphResponseBody";
export class BibfileService {
  /**
   * Generate Bibfile
   * @param requestBody
   * @returns GenerateBibfileSubgraphResponseBody Successful Response
   * @throws ApiError
   */
  public static generateBibfileAirasV1BibfileGenerationsPost(
    requestBody: GenerateBibfileSubgraphRequestBody,
  ): CancelablePromise<GenerateBibfileSubgraphResponseBody> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/airas/v1/bibfile/generations",
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    });
  }
}
