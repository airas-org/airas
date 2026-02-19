/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GitHubConfig } from './GitHubConfig';
import type { RunnerConfig } from './RunnerConfig';
import type { TopicOpenEndedResearchLLMMapping } from './TopicOpenEndedResearchLLMMapping';
import type { WandbConfig } from './WandbConfig';
export type TopicOpenEndedResearchRequestBody = {
    github_config: GitHubConfig;
    research_topic: string;
    runner_config: RunnerConfig;
    wandb_config: WandbConfig;
    is_github_repo_private?: boolean;
    search_method?: TopicOpenEndedResearchRequestBody.search_method;
    collection_name?: string;
    num_paper_search_queries?: number;
    papers_per_query?: number;
    hypothesis_refinement_iterations?: number;
    num_experiment_models?: number;
    num_experiment_datasets?: number;
    num_comparison_methods?: number;
    paper_content_refinement_iterations?: number;
    github_actions_agent?: TopicOpenEndedResearchRequestBody.github_actions_agent;
    latex_template_name?: string;
    llm_mapping?: (TopicOpenEndedResearchLLMMapping | null);
};
export namespace TopicOpenEndedResearchRequestBody {
    export enum search_method {
        AIRAS_DB = 'airas_db',
        QDRANT = 'qdrant',
    }
    export enum github_actions_agent {
        CLAUDE_CODE = 'claude_code',
        OPEN_CODE = 'open_code',
    }
}

