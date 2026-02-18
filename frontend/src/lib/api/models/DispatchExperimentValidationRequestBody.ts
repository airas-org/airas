/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DispatchExperimentValidationLLMMapping } from './DispatchExperimentValidationLLMMapping';
import type { ExperimentalDesign_Input } from './ExperimentalDesign_Input';
import type { GitHubConfig } from './GitHubConfig';
import type { ResearchHypothesis } from './ResearchHypothesis';
import type { WandbConfig } from './WandbConfig';
export type DispatchExperimentValidationRequestBody = {
    github_config: GitHubConfig;
    research_topic: string;
    run_id?: (string | null);
    workflow_run_id: number;
    run_stage: DispatchExperimentValidationRequestBody.run_stage;
    research_hypothesis: ResearchHypothesis;
    experimental_design: ExperimentalDesign_Input;
    wandb_config: WandbConfig;
    github_actions_agent?: DispatchExperimentValidationRequestBody.github_actions_agent;
    llm_mapping?: (DispatchExperimentValidationLLMMapping | null);
};
export namespace DispatchExperimentValidationRequestBody {
    export enum run_stage {
        SANITY = 'sanity',
        PILOT = 'pilot',
        MAIN = 'main',
        VISUALIZATION = 'visualization',
    }
    export enum github_actions_agent {
        CLAUDE_CODE = 'claude_code',
        OPEN_CODE = 'open_code',
    }
}

