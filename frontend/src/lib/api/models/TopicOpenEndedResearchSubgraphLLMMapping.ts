/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnalyzeExperimentLLMMapping } from './AnalyzeExperimentLLMMapping';
import type { CompileLatexLLMMapping } from './CompileLatexLLMMapping';
import type { DispatchCodeGenerationLLMMapping } from './DispatchCodeGenerationLLMMapping';
import type { DispatchExperimentValidationLLMMapping } from './DispatchExperimentValidationLLMMapping';
import type { GenerateExperimentalDesignLLMMapping } from './GenerateExperimentalDesignLLMMapping';
import type { GenerateHypothesisSubgraphV0LLMMapping } from './GenerateHypothesisSubgraphV0LLMMapping';
import type { GenerateLatexLLMMapping } from './GenerateLatexLLMMapping';
import type { GenerateQueriesLLMMapping } from './GenerateQueriesLLMMapping';
import type { RetrievePaperSubgraphLLMMapping } from './RetrievePaperSubgraphLLMMapping';
import type { SearchPaperTitlesFromQdrantLLMMapping } from './SearchPaperTitlesFromQdrantLLMMapping';
import type { WriteLLMMapping } from './WriteLLMMapping';
export type TopicOpenEndedResearchSubgraphLLMMapping = {
    generate_queries?: (GenerateQueriesLLMMapping | null);
    retrieve_paper?: (RetrievePaperSubgraphLLMMapping | null);
    generate_hypothesis?: (GenerateHypothesisSubgraphV0LLMMapping | null);
    generate_experimental_design?: (GenerateExperimentalDesignLLMMapping | null);
    dispatch_code_generation?: (DispatchCodeGenerationLLMMapping | null);
    dispatch_experiment_validation?: (DispatchExperimentValidationLLMMapping | null);
    analyze_experiment?: (AnalyzeExperimentLLMMapping | null);
    write?: (WriteLLMMapping | null);
    generate_latex?: (GenerateLatexLLMMapping | null);
    compile_latex?: (CompileLatexLLMMapping | null);
    search_paper_titles_from_qdrant?: (SearchPaperTitlesFromQdrantLLMMapping | null);
};

