/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type RunnerConfig = {
  /**
   * Runner labels used by GitHub Actions (e.g., ['ubuntu-latest'] or ['self-hosted', 'gpu-runner'])
   */
  runner_label: Array<string>;
  /**
   * Machine specifications and environment details for LLM to design appropriate experiments
   */
  description: string;
};
