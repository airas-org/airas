/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type FetchPaperFulltextResponseBody = {
    text: string;
    status: FetchPaperFulltextResponseBody.status;
    resolved_from: (string | null);
    execution_time: Record<string, Array<number>>;
};
export namespace FetchPaperFulltextResponseBody {
    export enum status {
        FULLTEXT = 'fulltext',
        ABSTRACT_ONLY = 'abstract_only',
        NOT_FOUND = 'not_found',
    }
}

