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
     * Result figure filenames (e.g. plot.pdf)
     */
    result_figures?: (Array<string> | null);
    /**
     * Method diagram filenames (e.g. architecture.pdf)
     */
    diagram_figures?: (Array<string> | null);
    /**
     * Metrics data for runs (keyed by run_id or 'comparison')
     */
    metrics_data?: (Record<string, any> | null);
};

