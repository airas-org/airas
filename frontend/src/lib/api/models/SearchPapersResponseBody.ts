/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PaperSearchResult } from './PaperSearchResult';
export type SearchPapersResponseBody = {
    papers: Array<PaperSearchResult>;
    source_results: Record<string, number>;
    search_errors: Record<string, string>;
    execution_time: Record<string, Array<number>>;
};

