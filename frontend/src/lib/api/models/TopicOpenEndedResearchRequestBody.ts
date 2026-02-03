/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GitHubConfig } from './GitHubConfig';
import type { RunnerConfig } from './RunnerConfig';
import type { TopicOpenEndedResearchSubgraphLLMMapping } from './TopicOpenEndedResearchSubgraphLLMMapping';
import type { WandbConfig } from './WandbConfig';
export type TopicOpenEndedResearchRequestBody = {
    github_config: GitHubConfig;
    research_topic: string;
    runner_config: RunnerConfig;
    wandb_config: WandbConfig;
    latex_template_name: TopicOpenEndedResearchRequestBody.latex_template_name;
    is_github_repo_private?: boolean;
    num_paper_search_queries?: number;
    papers_per_query?: number;
    hypothesis_refinement_iterations?: number;
    num_experiment_models?: number;
    num_experiment_datasets?: number;
    num_comparison_methods?: number;
    experiment_code_validation_iterations?: number;
    paper_content_refinement_iterations?: number;
    github_actions_latex_compile_agent?: TopicOpenEndedResearchRequestBody.github_actions_latex_compile_agent;
    llm_mapping?: (TopicOpenEndedResearchSubgraphLLMMapping | null);
};
export namespace TopicOpenEndedResearchRequestBody {
    export enum latex_template_name {
        ICLR2024 = 'iclr2024',
        AGENTS4SCIENCE_2025 = 'agents4science_2025',
        MDPI = 'mdpi',
    }
    export enum github_actions_latex_compile_agent {
        OPEN_CODE = 'open_code',
        CLAUDE_CODE = 'claude_code',
    }
}

