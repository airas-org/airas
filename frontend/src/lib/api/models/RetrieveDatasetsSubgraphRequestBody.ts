/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type RetrieveDatasetsSubgraphRequestBody = {
    dataset_subfield: RetrieveDatasetsSubgraphRequestBody.dataset_subfield;
};
export namespace RetrieveDatasetsSubgraphRequestBody {
    export enum dataset_subfield {
        INSTRUCTION_TUNING = 'instruction_tuning',
        REASONING_EVALUATION = 'reasoning_evaluation',
        NLP_TASKS = 'nlp_tasks',
        PROMPT_ENGINEERING = 'prompt_engineering',
        CODE_EVALUATION = 'code_evaluation',
        IMAGE_RECOGNITION = 'image_recognition',
        SPEECH = 'speech',
        VISION_LANGUAGE = 'vision_language',
    }
}

