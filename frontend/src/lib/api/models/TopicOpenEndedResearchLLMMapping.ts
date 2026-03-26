/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExperimentCycleGraphLLMMapping } from './ExperimentCycleGraphLLMMapping';
import type { GenerateExperimentalDesignLLMMapping } from './GenerateExperimentalDesignLLMMapping';
import type { GenerateHypothesisSubgraphV0LLMMapping } from './GenerateHypothesisSubgraphV0LLMMapping';
import type { GenerateQueriesLLMMapping } from './GenerateQueriesLLMMapping';
import type { LaTeXGraphLLMMapping } from './LaTeXGraphLLMMapping';
import type { RetrievePaperSubgraphLLMMapping } from './RetrievePaperSubgraphLLMMapping';
import type { SearchPaperTitlesFromQdrantLLMMapping } from './SearchPaperTitlesFromQdrantLLMMapping';
import type { WriteLLMMapping } from './WriteLLMMapping';
export type TopicOpenEndedResearchLLMMapping = {
    generate_queries?: (GenerateQueriesLLMMapping | null);
    retrieve_paper?: (RetrievePaperSubgraphLLMMapping | null);
    generate_hypothesis?: (GenerateHypothesisSubgraphV0LLMMapping | null);
    generate_experimental_design?: (GenerateExperimentalDesignLLMMapping | null);
    experiment_cycle?: (ExperimentCycleGraphLLMMapping | null);
    write?: (WriteLLMMapping | null);
    latex?: (LaTeXGraphLLMMapping | null);
    search_paper_titles_from_qdrant?: (SearchPaperTitlesFromQdrantLLMMapping | null);
};

