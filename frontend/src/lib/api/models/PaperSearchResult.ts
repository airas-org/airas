/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * A paper found by any search source, normalized to a common shape.
 */
export type PaperSearchResult = {
    title: string;
    authors?: Array<string>;
    abstract?: (string | null);
    doi?: (string | null);
    arxiv_id?: (string | null);
    url?: (string | null);
    pdf_url?: (string | null);
    published_date?: (string | null);
    venue?: (string | null);
    citations?: (number | null);
    source: string;
    external_ids?: Record<string, string>;
};

