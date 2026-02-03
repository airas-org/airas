/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GenerateLatexLLMMapping } from './GenerateLatexLLMMapping';
import type { PaperContent } from './PaperContent';
export type GenerateLatexSubgraphRequestBody = {
    references_bib: string;
    paper_content: PaperContent;
    latex_template_name?: GenerateLatexSubgraphRequestBody.latex_template_name;
    llm_mapping?: (GenerateLatexLLMMapping | null);
};
export namespace GenerateLatexSubgraphRequestBody {
    export enum latex_template_name {
        ICLR2024 = 'iclr2024',
        AGENTS4SCIENCE_2025 = 'agents4science_2025',
        MDPI = 'MDPI',
    }
}

