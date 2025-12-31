/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type SearchSpace = {
  /**
   * Parameter name to optimize
   */
  param_name: string;
  /**
   * Distribution type: 'loguniform', 'uniform', 'int', or 'categorical'
   */
  distribution_type: string;
  /**
   * Lower bound for continuous/integer distributions
   */
  low?: number | null;
  /**
   * Upper bound for continuous/integer distributions
   */
  high?: number | null;
  /**
   * Choices for categorical distribution
   */
  choices?: null;
};
