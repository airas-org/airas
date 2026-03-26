/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExperimentCycle_Input } from './ExperimentCycle_Input';
export type ExperimentHistory_Input = {
    /**
     * Append-only list of experiment cycles (pilot and full only; sanity is not recorded)
     */
    cycles?: Array<ExperimentCycle_Input>;
};

