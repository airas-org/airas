/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type DatasetConfig = {
    description: string;
    num_training_samples: (number | string);
    num_validation_samples: (number | string);
    huggingface_url: string;
    dependent_packages: Array<string>;
    code: string;
    citation: string;
    task_type: Array<(string | 'object-detection' | 'semantic-segmentation' | 'instance-segmentation' | 'panoptic-segmentation' | 'video-object-segmentation' | 'image-classification' | 'image-captioning' | 'image-embeddings' | 'face-detection' | 'face-verification' | 'face-identification' | 'few-shot-classification' | 'one-shot-classification' | 'facial-expression-recognition' | 'valence-arousal-prediction')>;
    language_distribution?: (string | null);
    image_size?: (string | null);
    sample_data?: (Record<string, any> | null);
};

