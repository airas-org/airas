/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DispatchCodeGenerationLLMMapping } from './DispatchCodeGenerationLLMMapping';
import type { ExperimentalDesign_Input } from './ExperimentalDesign_Input';
import type { GitHubConfig } from './GitHubConfig';
import type { ResearchHypothesis } from './ResearchHypothesis';
import type { WandbConfig } from './WandbConfig';
export type DispatchCodeGenerationRequestBody = {
    github_config: GitHubConfig;
    research_topic: string;
    research_hypothesis: ResearchHypothesis;
    experimental_design: ExperimentalDesign_Input;
    wandb_config: WandbConfig;
    github_actions_agent?: DispatchCodeGenerationRequestBody.github_actions_agent;
    llm_mapping?: (DispatchCodeGenerationLLMMapping | null);
};
export namespace DispatchCodeGenerationRequestBody {
    export enum github_actions_agent {
        CLAUDE_CODE = 'claude_code',
        OPEN_CODE = 'open_code',
    }
}

