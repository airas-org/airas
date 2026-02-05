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
    is_github_repo_private?: boolean;
    num_paper_search_queries?: number;
    papers_per_query?: number;
    hypothesis_refinement_iterations?: number;
    num_experiment_models?: number;
    num_experiment_datasets?: number;
    num_comparison_methods?: number;
    experiment_code_validation_iterations?: number;
    paper_content_refinement_iterations?: number;
    latex_template_name?: string;
    github_actions_agent?: string;
    llm_mapping?: (TopicOpenEndedResearchSubgraphLLMMapping | null);
};

