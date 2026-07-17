/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CompileLatexSubgraphRequestBody } from '../models/CompileLatexSubgraphRequestBody';
import type { CompileLatexSubgraphResponseBody } from '../models/CompileLatexSubgraphResponseBody';
import type { GenerateLatexSubgraphRequestBody } from '../models/GenerateLatexSubgraphRequestBody';
import type { GenerateLatexSubgraphResponseBody } from '../models/GenerateLatexSubgraphResponseBody';
import type { PushLatexSubgraphRequestBody } from '../models/PushLatexSubgraphRequestBody';
import type { PushLatexSubgraphResponseBody } from '../models/PushLatexSubgraphResponseBody';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class LatexService {
    /**
     * Generate Latex
     * @param requestBody
     * @returns GenerateLatexSubgraphResponseBody Successful Response
     * @throws ApiError
     */
    public static generateLatexAirasV1LatexGenerationsPost(
        requestBody: GenerateLatexSubgraphRequestBody,
    ): CancelablePromise<GenerateLatexSubgraphResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/latex/generations',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Push Latex
     * @param requestBody
     * @returns PushLatexSubgraphResponseBody Successful Response
     * @throws ApiError
     */
    public static pushLatexAirasV1LatexPushPost(
        requestBody: PushLatexSubgraphRequestBody,
    ): CancelablePromise<PushLatexSubgraphResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/latex/push',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Open In Overleaf
     * Serve a page that forwards the paper's LaTeX project to Overleaf.
     *
     * Opened in a browser (not called as a JSON API): the page carries the
     * zipped LaTeX sources inline and immediately POSTs them to Overleaf,
     * which creates a new project in the user's Overleaf account.
     * @param githubOwner
     * @param repositoryName
     * @param branchName
     * @param latexTemplateName
     * @returns string Successful Response
     * @throws ApiError
     */
    public static openInOverleafAirasV1LatexOverleafGet(
        githubOwner: string,
        repositoryName: string,
        branchName: string,
        latexTemplateName: 'iclr2024' | 'agents4science_2025' | 'mdpi' = 'mdpi',
    ): CancelablePromise<string> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/airas/v1/latex/overleaf',
            query: {
                'github_owner': githubOwner,
                'repository_name': repositoryName,
                'branch_name': branchName,
                'latex_template_name': latexTemplateName,
            },
            errors: {
                404: `LaTeX project not found in the repository (push_latex has not been run)`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Compile Latex
     * @param requestBody
     * @returns CompileLatexSubgraphResponseBody Successful Response
     * @throws ApiError
     */
    public static compileLatexAirasV1LatexCompilePost(
        requestBody: CompileLatexSubgraphRequestBody,
    ): CancelablePromise<CompileLatexSubgraphResponseBody> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/airas/v1/latex/compile',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
