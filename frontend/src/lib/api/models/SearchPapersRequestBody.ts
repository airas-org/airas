/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type SearchPapersRequestBody = {
    query: string;
    sources?: Array<string>;
    max_results_per_source?: number;
    year?: (string | null);
    search_mode?: SearchPapersRequestBody.search_mode;
};
export namespace SearchPapersRequestBody {
    export enum search_mode {
        KEYWORD = 'keyword',
        SEMANTIC = 'semantic',
    }
}

