/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExperimentCycle_Output } from './ExperimentCycle_Output';
export type ExperimentHistory_Output = {
    /**
     * Append-only list of experiment cycles (pilot and main only; sanity is not recorded)
     */
    cycles?: Array<ExperimentCycle_Output>;
};

