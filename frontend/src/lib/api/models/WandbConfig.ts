/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type WandbConfig = {
  /**
   * Wandb entity (username or team name)
   */
  entity: string;
  /**
   * Wandb project name
   */
  project: string;
  /**
   * List of Wandb run IDs (optional, can be retrieved from metadata)
   */
  run_ids?: Array<string> | null;
};
