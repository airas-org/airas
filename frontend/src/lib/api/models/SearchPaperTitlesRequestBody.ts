/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type SearchPaperTitlesRequestBody = {
    search_method?: SearchPaperTitlesRequestBody.search_method;
    queries: Array<string>;
    max_results_per_query?: number;
    collection_name?: string;
};
export namespace SearchPaperTitlesRequestBody {
    export enum search_method {
        AIRAS_DB = 'airas_db',
        QDRANT = 'qdrant',
    }
}

