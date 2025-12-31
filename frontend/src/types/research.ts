export interface ResearchSection {
  id: string;
  title: string;
  createdAt: Date;
  status: "in-progress" | "completed";
}

export interface Paper {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  year: number;
  citations: number;
  relevanceScore: number;
}

export interface Method {
  id: string;
  name: string;
  description: string;
  basedOn: string[];
}

export interface ExperimentConfig {
  id: string;
  model: string;
  dataset: string;
  hyperparameters: Record<string, string | number>;
  description: string;
}

export interface ExperimentResult {
  id: string;
  configId: string;
  metrics: Record<string, number>;
  status: "pending" | "running" | "completed" | "failed";
  logs?: string;
}

export interface GeneratedPaper {
  title: string;
  abstract: string;
  sections: {
    name: string;
    content: string;
  }[];
}

export type FeatureType =
  | "papers"
  | "method"
  | "experiment-config"
  | "code-generation"
  | "experiment-run"
  | "analysis"
  | "paper-writing";

export interface WorkflowNode {
  id: string;
  type: FeatureType;
  branchIndex: number; // 0 = main branch, 1+ = branches
  parentId: string | null;
  children: string[]; // child node ids
  data?: {
    selectedPapers?: Paper[];
    generatedMethod?: Method | null;
    experimentConfigs?: ExperimentConfig[];
    githubUrl?: string | null;
    experimentResults?: ExperimentResult[];
    analysisText?: string | null;
    generatedPaper?: GeneratedPaper | null;
  };
  snapshot?: {
    selectedPapers: Paper[];
    generatedMethod: Method | null;
    experimentConfigs: ExperimentConfig[];
    githubUrl: string | null;
    experimentResults: ExperimentResult[];
    analysisText: string | null;
    generatedPaper: GeneratedPaper | null;
  };
  createdAt: Date;
}

export interface WorkflowTree {
  nodes: Record<string, WorkflowNode>;
  rootId: string | null;
  activeNodeId: string | null;
}
