/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type TrainingConfig = {
    /**
     * Learning rate for training
     */
    learning_rate?: (number | null);
    /**
     * Batch size for training
     */
    batch_size?: (number | null);
    /**
     * Number of training epochs
     */
    epochs?: (number | null);
    /**
     * Optimizer (e.g., 'adam', 'adamw', 'sgd')
     */
    optimizer?: (string | null);
    /**
     * Number of warmup steps for learning rate scheduler
     */
    warmup_steps?: (number | null);
    /**
     * Weight decay for regularization
     */
    weight_decay?: (number | null);
    /**
     * Gradient clipping value to prevent exploding gradients
     */
    gradient_clip?: (number | null);
    /**
     * Learning rate scheduler (e.g., 'linear', 'cosine')
     */
    scheduler?: (string | null);
    /**
     * Random seed for reproducibility
     */
    seed?: number;
    /**
     * Additional experiment-specific parameters
     */
    additional_params?: (string | null);
};

