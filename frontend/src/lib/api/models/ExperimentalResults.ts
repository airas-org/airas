/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ExperimentalResults = {
    /**
     * Standard output from the run
     */
    stdout?: (string | null);
    /**
     * Standard error from the run
     */
    stderr?: (string | null);
    /**
     * Result figure paths relative to the results directory, which is also their path under the paper's images/ (e.g. run-1/plot.pdf is referenced as images/run-1/plot.pdf)
     */
    result_figures?: (Array<string> | null);
    /**
     * Method diagram paths, relative in the same way as result_figures (e.g. diagram/architecture.pdf)
     */
    diagram_figures?: (Array<string> | null);
    /**
     * Metrics data for runs (keyed by run_id or 'comparison')
     */
    metrics_data?: (Record<string, any> | null);
};

