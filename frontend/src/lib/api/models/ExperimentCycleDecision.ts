/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExperimentCycleAction } from './ExperimentCycleAction';
export type ExperimentCycleDecision = {
    /**
     * The decided next action for the experiment cycle
     */
    action: ExperimentCycleAction;
    /**
     * Explanation of why this action was chosen
     */
    reasoning?: (string | null);
    /**
     * Instruction for refining the experimental design. Required when action is redesign.
     */
    design_instruction?: (string | null);
};

