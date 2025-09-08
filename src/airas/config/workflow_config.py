from dataclasses import dataclass


@dataclass
class WorkflowLoopConfig:
    max_fix_attempts: int = 8
    max_consistency_attempts: int = 1


DEFAULT_WORKFLOW_CONFIG = WorkflowLoopConfig()
