/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SearchSpace } from './SearchSpace';
export type OptunaConfig = {
    /**
     * Whether to enable Optuna optimization
     */
    enabled?: boolean;
    /**
     * Number of Optuna trials to run
     */
    n_trials?: number;
    /**
     * Hyperparameter search space definitions
     */
    search_spaces?: (Array<SearchSpace> | null);
};

