/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LLMExtractedInfo } from './LLMExtractedInfo';
import type { MetaData } from './MetaData';
/**
 * One prior study, as the generation prompts consume it.
 *
 * Only `title` is required. The rest default to empty so a study can be
 * assembled by hand from a `search_papers` row — which is the documented
 * path whenever `retrieve_papers` is unavailable — without inventing a
 * full text or a reference list that the caller does not have.
 */
export type ResearchStudy = {
    title: string;
    /**
     * The study's abstract. Populated directly from a search result; the only summary available when no full text was retrieved.
     */
    abstract?: (string | null);
    full_text?: string;
    references?: Array<string>;
    meta_data?: MetaData;
    llm_extracted_info?: LLMExtractedInfo;
};

