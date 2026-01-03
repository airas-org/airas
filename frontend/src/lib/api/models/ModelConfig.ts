/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ModelParameters } from './ModelParameters';
export type ModelConfig = {
    model_parameters: (ModelParameters | string);
    model_architecture: string;
    training_data_sources: (string | null);
    huggingface_url: string;
    input_modalities: Array<'text' | 'image' | 'audio' | 'video' | 'tabular' | 'time_series' | 'graph' | 'embeddings'>;
    dependent_packages: Array<string>;
    code: string;
    citation: string;
    task_type: (string | 'object-detection' | 'semantic-segmentation' | 'instance-segmentation' | 'panoptic-segmentation' | 'video-object-segmentation' | 'image-classification' | 'image-captioning' | 'image-embeddings' | 'face-detection' | 'face-verification' | 'face-identification' | 'few-shot-classification' | 'one-shot-classification' | 'facial-expression-recognition' | 'valence-arousal-prediction');
    output_modalities?: (Array<'text' | 'image' | 'audio' | 'video' | 'tabular' | 'time_series' | 'graph' | 'embeddings'> | null);
    language_distribution?: (string | null);
    image_size?: (string | null);
};

