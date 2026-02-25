/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GitHubConfig } from './GitHubConfig';
import type { HypothesisDrivenResearchLLMMapping } from './HypothesisDrivenResearchLLMMapping';
import type { ResearchHypothesis } from './ResearchHypothesis';
import type { RunnerConfig } from './RunnerConfig';
import type { WandbConfig } from './WandbConfig';
export type HypothesisDrivenResearchRequestBody = {
    github_config: GitHubConfig;
    research_hypothesis: ResearchHypothesis;
    research_topic?: string;
    runner_config: RunnerConfig;
    wandb_config: WandbConfig;
    is_github_repo_private?: boolean;
    num_experiment_models?: number;
    num_experiment_datasets?: number;
    num_comparison_methods?: number;
    paper_content_refinement_iterations?: number;
    github_actions_agent?: HypothesisDrivenResearchRequestBody.github_actions_agent;
    latex_template_name?: string;
    llm_mapping?: (HypothesisDrivenResearchLLMMapping | null);
};
export namespace HypothesisDrivenResearchRequestBody {
    export enum github_actions_agent {
        CLAUDE_CODE = 'claude_code',
        OPEN_CODE = 'open_code',
    }
}

