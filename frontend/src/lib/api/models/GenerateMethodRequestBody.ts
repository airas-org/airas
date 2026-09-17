/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GenerateVerificationMethodLLMMapping } from './GenerateVerificationMethodLLMMapping';
import type { ProposedMethodSchema } from './ProposedMethodSchema';
export type GenerateMethodRequestBody = {
    user_query: string;
    selected_policy: ProposedMethodSchema;
    llm_mapping?: (GenerateVerificationMethodLLMMapping | null);
    verification_id?: (string | null);
};

