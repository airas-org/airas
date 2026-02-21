/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExperimentalAnalysis } from './ExperimentalAnalysis';
import type { ExperimentalDesign_Output } from './ExperimentalDesign_Output';
import type { ExperimentalResults } from './ExperimentalResults';
import type { ExperimentCode } from './ExperimentCode';
import type { PaperContent } from './PaperContent';
import type { PaperReviewScores } from './PaperReviewScores';
import type { ResearchHypothesis } from './ResearchHypothesis';
import type { ResearchStudy } from './ResearchStudy';
export type ResearchHistory_Output = {
    /**
     * Main research topic
     */
    research_topic?: (string | null);
    /**
     * List of search queries used for paper retrieval
     */
    queries?: (Array<string> | null);
    /**
     * List of main research studies analyzed
     */
    research_study_list?: (Array<ResearchStudy> | null);
    /**
     * Research hypothesis generated
     */
    research_hypothesis?: (ResearchHypothesis | null);
    /**
     * Experimental design and methodology
     */
    experimental_design?: (ExperimentalDesign_Output | null);
    /**
     * Generated experiment code and implementation
     */
    experiment_code?: (ExperimentCode | null);
    /**
     * Results from running experiments
     */
    experimental_results?: (ExperimentalResults | null);
    /**
     * Analysis and interpretation of experimental results
     */
    experimental_analysis?: (ExperimentalAnalysis | null);
    /**
     * Generated paper content including sections and text
     */
    paper_content?: (PaperContent | null);
    /**
     * Bibliography references in BibTeX format
     */
    references_bib?: (string | null);
    /**
     * LaTeX formatted paper text
     */
    latex_text?: (string | null);
    /**
     * URL to the published or hosted paper
     */
    paper_url?: (string | null);
    /**
     * Full HTML content of the generated paper
     */
    full_html?: (string | null);
    /**
     * GitHub Pages URL for the published paper
     */
    github_pages_url?: (string | null);
    /**
     * Review scores and feedback for the paper
     */
    paper_review_scores?: (PaperReviewScores | null);
    /**
     * Additional data fields for future extensions
     */
    additional_data?: (Record<string, any> | null);
};

