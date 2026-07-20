/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type RetrieveModelsSubgraphRequestBody = {
    model_subfield: RetrieveModelsSubgraphRequestBody.model_subfield;
};
export namespace RetrieveModelsSubgraphRequestBody {
    export enum model_subfield {
        TEXT_GENERATION = 'text_generation',
        TEXT_UNDERSTANDING = 'text_understanding',
        SEQUENCE_TO_SEQUENCE = 'sequence_to_sequence',
        CODE_GENERATION = 'code_generation',
        TEXT_EMBEDDING = 'text_embedding',
        RERANKING = 'reranking',
        HOSTED_API = 'hosted_api',
        IMAGE_RECOGNITION = 'image_recognition',
        IMAGE_GENERATION = 'image_generation',
        VISION_LANGUAGE = 'vision_language',
        SPEECH = 'speech',
        FORECASTING = 'forecasting',
        PROTEIN = 'protein',
    }
}

