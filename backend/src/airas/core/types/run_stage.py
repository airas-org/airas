from enum import Enum


class RunStage(str, Enum):
    SANITY = "sanity"
    PILOT = "pilot"
    FULL = "full"
    VISUALIZATION = "visualization"
