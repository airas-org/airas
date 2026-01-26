/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnthropicParams } from './AnthropicParams';
import type { GoogleGenAIParams } from './GoogleGenAIParams';
import type { OpenAIParams } from './OpenAIParams';
export type NodeLLMConfig = {
    llm_name: string;
    params?: ((OpenAIParams | GoogleGenAIParams | AnthropicParams) | null);
};

