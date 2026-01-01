from dataclasses import dataclass


@dataclass
class WorkflowLoopConfig:
    max_fix_attempts: int = 10
    max_consistency_attempts: int = 3


DEFAULT_WORKFLOW_CONFIG = WorkflowLoopConfig()
