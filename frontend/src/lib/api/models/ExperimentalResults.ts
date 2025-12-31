/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ExperimentalResults = {
  /**
   * Standard output from the run
   */
  stdout?: string | null;
  /**
   * Standard error from the run
   */
  stderr?: string | null;
  /**
   * Figures specific to this run
   */
  figures?: Array<string> | null;
  /**
   * Metrics data for runs (keyed by run_id or 'comparison')
   */
  metrics_data?: Record<string, any> | null;
};
