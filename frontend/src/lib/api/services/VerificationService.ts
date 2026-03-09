/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExperimentCodeStatusResponseBody } from '../models/ExperimentCodeStatusResponseBody';
import type { GenerateExperimentCodeRequestBody } from '../models/GenerateExperimentCodeRequestBody';
import type { GenerateExperimentCodeResponseBody } from '../models/GenerateExperimentCodeResponseBody';
import type { GenerateMethodRequestBody } from '../models/GenerateMethodRequestBody';
import type { GenerateMethodResponseBody } from '../models/GenerateMethodResponseBody';
import type { ProposePoliciesRequestBody } from '../models/ProposePoliciesRequestBody';
import type { ProposePoliciesResponseBody } from '../models/ProposePoliciesResponseBody';
import type { VerificationSessionCreateRequest } from '../models/VerificationSessionCreateRequest';
import type { VerificationSessionListResponse } from '../models/VerificationSessionListResponse';
import type { VerificationSessionResponse } from '../models/VerificationSessionResponse';
import type { VerificationSessionUpdateRequest } from '../models/VerificationSessionUpdateRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class VerificationService {
    /**
     * List Sessions
     * @returns VerificationSessionListResponse Successful Response
     * @throws ApiError
     */
    public static listSessionsAirasV1VerificationSessionsGet(): CancelablePromise<VerificationSessionListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/v1/verification/sessions',
        });
    }
    /**
     * Create Session
     * @param requestBody
     * @returns VerificationSessionResponse Successful Response
     * @throws ApiError
     */
    public static createSessionAirasV1VerificationSessionsPost(
        requestBody: VerificationSessionCreateRequest,
    ): CancelablePromise<VerificationSessionResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/verification/sessions',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Session
     * @param verificationId
     * @returns VerificationSessionResponse Successful Response
     * @throws ApiError
     */
    public static getSessionAirasV1VerificationSessionsVerificationIdGet(
        verificationId: string,
    ): CancelablePromise<VerificationSessionResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/v1/verification/sessions/{verification_id}',
            path: {
                'verification_id': verificationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Session
     * @param verificationId
     * @param requestBody
     * @returns VerificationSessionResponse Successful Response
     * @throws ApiError
     */
    public static updateSessionAirasV1VerificationSessionsVerificationIdPatch(
        verificationId: string,
        requestBody: VerificationSessionUpdateRequest,
    ): CancelablePromise<VerificationSessionResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/airas/v1/verification/sessions/{verification_id}',
            path: {
                'verification_id': verificationId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Session
     * @param verificationId
     * @returns void
     * @throws ApiError
     */
    public static deleteSessionAirasV1VerificationSessionsVerificationIdDelete(
        verificationId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/airas/v1/verification/sessions/{verification_id}',
            path: {
                'verification_id': verificationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Propose Policies
     * @param requestBody
     * @returns ProposePoliciesResponseBody Successful Response
     * @throws ApiError
     */
    public static proposePoliciesAirasV1VerificationProposePoliciesPost(
        requestBody: ProposePoliciesRequestBody,
    ): CancelablePromise<ProposePoliciesResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/verification/propose-policies',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Generate Method
     * @param requestBody
     * @returns GenerateMethodResponseBody Successful Response
     * @throws ApiError
     */
    public static generateMethodAirasV1VerificationGenerateMethodPost(
        requestBody: GenerateMethodRequestBody,
    ): CancelablePromise<GenerateMethodResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/verification/generate-method',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Generate Experiment Code
     * @param requestBody
     * @param xGithubSession
     * @returns GenerateExperimentCodeResponseBody Successful Response
     * @throws ApiError
     */
    public static generateExperimentCodeAirasV1VerificationGenerateExperimentCodePost(
        requestBody: GenerateExperimentCodeRequestBody,
        xGithubSession?: (string | null),
    ): CancelablePromise<GenerateExperimentCodeResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/verification/generate-experiment-code',
            headers: {
                'x-github-session': xGithubSession,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Experiment Code Status
     * @param githubOwner
     * @param repositoryName
     * @param workflowRunId
     * @param xGithubSession
     * @returns ExperimentCodeStatusResponseBody Successful Response
     * @throws ApiError
     */
    public static getExperimentCodeStatusAirasV1VerificationExperimentCodeStatusGithubOwnerRepositoryNameWorkflowRunIdGet(
        githubOwner: string,
        repositoryName: string,
        workflowRunId: number,
        xGithubSession?: (string | null),
    ): CancelablePromise<ExperimentCodeStatusResponseBody> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/v1/verification/experiment-code-status/{github_owner}/{repository_name}/{workflow_run_id}',
            path: {
                'github_owner': githubOwner,
                'repository_name': repositoryName,
                'workflow_run_id': workflowRunId,
            },
            headers: {
                'x-github-session': xGithubSession,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
