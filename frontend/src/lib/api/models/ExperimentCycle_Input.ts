/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExperimentalAnalysis } from './ExperimentalAnalysis';
import type { ExperimentalDesign_Input } from './ExperimentalDesign_Input';
import type { ExperimentalResults } from './ExperimentalResults';
import type { ExperimentCycleDecision } from './ExperimentCycleDecision';
import type { RunStage } from './RunStage';
export type ExperimentCycle_Input = {
    /**
     * Experimental design used in this cycle
     */
    experimental_design: ExperimentalDesign_Input;
    /**
     * Stage at which the experiment was executed (pilot or full)
     */
    run_stage: RunStage;
    /**
     * Results from the experiment execution
     */
    experimental_results?: (ExperimentalResults | null);
    /**
     * Analysis of the experiment results
     */
    experimental_analysis?: (ExperimentalAnalysis | null);
    /**
     * Decision made after analyzing this cycle's results
     */
    decision?: (ExperimentCycleDecision | null);
};

