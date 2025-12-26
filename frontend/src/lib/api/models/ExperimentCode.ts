/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ExperimentCode = {
    train_py?: string;
    evaluate_py?: string;
    preprocess_py?: string;
    model_py?: string;
    main_py?: string;
    pyproject_toml?: string;
    config_yaml?: string;
    /**
     * Run configuration YAMLs keyed by run_id
     */
    run_configs?: (Record<string, string> | null);
};

