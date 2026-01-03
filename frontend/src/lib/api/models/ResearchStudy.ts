/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LLMExtractedInfo } from './LLMExtractedInfo';
import type { MetaData } from './MetaData';
export type ResearchStudy = {
    title: string;
    full_text: string;
    references: Array<string>;
    meta_data: MetaData;
    llm_extracted_info: LLMExtractedInfo;
};

