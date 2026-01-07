/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnalyzeExperimentLLMMapping } from './AnalyzeExperimentLLMMapping';
import type { GenerateCodeLLMMapping } from './GenerateCodeLLMMapping';
import type { GenerateExperimentalDesignLLMMapping } from './GenerateExperimentalDesignLLMMapping';
import type { GenerateHypothesisSubgraphV0LLMMapping } from './GenerateHypothesisSubgraphV0LLMMapping';
import type { GenerateLatexLLMMapping } from './GenerateLatexLLMMapping';
import type { GenerateQueriesLLMMapping } from './GenerateQueriesLLMMapping';
import type { RetrievePaperSubgraphLLMMapping } from './RetrievePaperSubgraphLLMMapping';
import type { WriteLLMMapping } from './WriteLLMMapping';
export type TopicOpenEndedResearchSubgraphLLMMapping = {
    generate_queries?: (GenerateQueriesLLMMapping | null);
    retrieve_paper?: (RetrievePaperSubgraphLLMMapping | null);
    generate_hypothesis?: (GenerateHypothesisSubgraphV0LLMMapping | null);
    generate_experimental_design?: (GenerateExperimentalDesignLLMMapping | null);
    generate_code?: (GenerateCodeLLMMapping | null);
    analyze_experiment?: (AnalyzeExperimentLLMMapping | null);
    write?: (WriteLLMMapping | null);
    generate_latex?: (GenerateLatexLLMMapping | null);
};

