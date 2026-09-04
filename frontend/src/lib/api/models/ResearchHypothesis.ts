/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ResearchHypothesis = {
    open_problems: string;
    method: string;
    experimental_setup: string;
    /**
     * One standard, machine-extractable metric name. The GAP between the proposal and its baselines is computed from this one.
     */
    primary_metric: string;
    /**
     * Further metric names reported alongside the primary one, for research whose claim needs more than a single number. Reported separately; never aggregated into primary_metric.
     */
    supporting_metrics?: Array<string>;
    experimental_code?: string;
    expected_result: string;
    expected_conclusion: string;
};

