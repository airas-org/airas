/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExperimentalDesign_Input } from "./ExperimentalDesign_Input";
import type { GenerateCodeLLMMapping } from "./GenerateCodeLLMMapping";
import type { ResearchHypothesis } from "./ResearchHypothesis";
import type { WandbConfig } from "./WandbConfig";
export type GenerateCodeSubgraphRequestBody = {
  research_hypothesis: ResearchHypothesis;
  experimental_design: ExperimentalDesign_Input;
  wandb_config: WandbConfig;
  max_code_validations: number;
  llm_mapping?: GenerateCodeLLMMapping | null;
};
