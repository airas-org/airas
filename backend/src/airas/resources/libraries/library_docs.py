# Canonical documentation endpoints for AI-research libraries, organized
# as a shared domain>category tree mirroring resources/models and
# resources/datasets. Agents fetch living docs (llms_txt where published)
# at experiment time instead of vendoring copies. To add a library: edit
# the relevant domain/<category>.py (verify URLs first) — the weekly
# link-check workflow guards against rot.
from airas.resources.libraries.audio.audio import AUDIO_LIBRARIES
from airas.resources.libraries.decision_science.decision_making import (
    DECISION_MAKING_LIBRARIES,
)
from airas.resources.libraries.decision_science.mathematical_optimization import (
    MATHEMATICAL_OPTIMIZATION_LIBRARIES,
)
from airas.resources.libraries.foundations.core import CORE_LIBRARIES
from airas.resources.libraries.foundations.jax_ecosystem import JAX_ECOSYSTEM_LIBRARIES
from airas.resources.libraries.graph.graph_learning import GRAPH_LEARNING_LIBRARIES
from airas.resources.libraries.graph.network_analysis import NETWORK_ANALYSIS_LIBRARIES
from airas.resources.libraries.interpretability.explainable_ai import (
    EXPLAINABLE_AI_LIBRARIES,
)
from airas.resources.libraries.interpretability.mechanistic import MECHANISTIC_LIBRARIES
from airas.resources.libraries.language.architecture_research import (
    ARCHITECTURE_RESEARCH_LIBRARIES,
)
from airas.resources.libraries.language.evaluation import EVALUATION_LIBRARIES
from airas.resources.libraries.language.fine_tuning import FINE_TUNING_LIBRARIES
from airas.resources.libraries.language.nlp import NLP_LIBRARIES
from airas.resources.libraries.language.orchestration import ORCHESTRATION_LIBRARIES
from airas.resources.libraries.language.post_training import POST_TRAINING_LIBRARIES
from airas.resources.libraries.language.rag_retrieval import RAG_RETRIEVAL_LIBRARIES
from airas.resources.libraries.language.safety import SAFETY_LIBRARIES
from airas.resources.libraries.language.structured_output import (
    STRUCTURED_OUTPUT_LIBRARIES,
)
from airas.resources.libraries.language.tokenization import TOKENIZATION_LIBRARIES
from airas.resources.libraries.machine_learning.anomaly_detection import (
    ANOMALY_DETECTION_LIBRARIES,
)
from airas.resources.libraries.machine_learning.hyperparameter_optimization import (
    HYPERPARAMETER_OPTIMIZATION_LIBRARIES,
)
from airas.resources.libraries.machine_learning.recommender_systems import (
    RECOMMENDER_SYSTEMS_LIBRARIES,
)
from airas.resources.libraries.machine_learning.statistical_ml import (
    STATISTICAL_ML_LIBRARIES,
)
from airas.resources.libraries.multimodal.vision_language import (
    VISION_LANGUAGE_LIBRARIES,
)
from airas.resources.libraries.reinforcement_learning.reinforcement_learning import (
    REINFORCEMENT_LEARNING_LIBRARIES,
)
from airas.resources.libraries.reinforcement_learning.simulation import (
    SIMULATION_LIBRARIES,
)
from airas.resources.libraries.reinforcement_learning.vla import VLA_LIBRARIES
from airas.resources.libraries.reinforcement_learning.world_models import (
    WORLD_MODELS_LIBRARIES,
)
from airas.resources.libraries.science.bioinformatics import BIOINFORMATICS_LIBRARIES
from airas.resources.libraries.science.chemistry_materials import (
    CHEMISTRY_MATERIALS_LIBRARIES,
)
from airas.resources.libraries.science.medical import MEDICAL_LIBRARIES
from airas.resources.libraries.science.physics import PHYSICS_LIBRARIES
from airas.resources.libraries.science.quantum_computing import (
    QUANTUM_COMPUTING_LIBRARIES,
)
from airas.resources.libraries.statistics.bayesian_inference import (
    BAYESIAN_INFERENCE_LIBRARIES,
)
from airas.resources.libraries.statistics.causal_inference import (
    CAUSAL_INFERENCE_LIBRARIES,
)
from airas.resources.libraries.statistics.experimental_design import (
    EXPERIMENTAL_DESIGN_LIBRARIES,
)
from airas.resources.libraries.statistics.spatial_statistics import (
    SPATIAL_STATISTICS_LIBRARIES,
)
from airas.resources.libraries.statistics.statistical_analysis import (
    STATISTICAL_ANALYSIS_LIBRARIES,
)
from airas.resources.libraries.statistics.survival_analysis import (
    SURVIVAL_ANALYSIS_LIBRARIES,
)
from airas.resources.libraries.systems.data_processing import DATA_PROCESSING_LIBRARIES
from airas.resources.libraries.systems.distributed_training import (
    DISTRIBUTED_TRAINING_LIBRARIES,
)
from airas.resources.libraries.systems.experiment_tracking import (
    EXPERIMENT_TRACKING_LIBRARIES,
)
from airas.resources.libraries.systems.gpu_computing import GPU_COMPUTING_LIBRARIES
from airas.resources.libraries.systems.inference_serving import (
    INFERENCE_SERVING_LIBRARIES,
)
from airas.resources.libraries.systems.model_compression import (
    MODEL_COMPRESSION_LIBRARIES,
)
from airas.resources.libraries.time_series.time_series import TIME_SERIES_LIBRARIES
from airas.resources.libraries.vision.vision import VISION_LIBRARIES

_CATEGORY_REGISTRIES = [
    ANOMALY_DETECTION_LIBRARIES,
    ARCHITECTURE_RESEARCH_LIBRARIES,
    AUDIO_LIBRARIES,
    BAYESIAN_INFERENCE_LIBRARIES,
    BIOINFORMATICS_LIBRARIES,
    CAUSAL_INFERENCE_LIBRARIES,
    CHEMISTRY_MATERIALS_LIBRARIES,
    CORE_LIBRARIES,
    DATA_PROCESSING_LIBRARIES,
    DECISION_MAKING_LIBRARIES,
    DISTRIBUTED_TRAINING_LIBRARIES,
    EVALUATION_LIBRARIES,
    EXPERIMENTAL_DESIGN_LIBRARIES,
    EXPERIMENT_TRACKING_LIBRARIES,
    EXPLAINABLE_AI_LIBRARIES,
    FINE_TUNING_LIBRARIES,
    GPU_COMPUTING_LIBRARIES,
    GRAPH_LEARNING_LIBRARIES,
    HYPERPARAMETER_OPTIMIZATION_LIBRARIES,
    INFERENCE_SERVING_LIBRARIES,
    JAX_ECOSYSTEM_LIBRARIES,
    MATHEMATICAL_OPTIMIZATION_LIBRARIES,
    MECHANISTIC_LIBRARIES,
    MEDICAL_LIBRARIES,
    MODEL_COMPRESSION_LIBRARIES,
    NETWORK_ANALYSIS_LIBRARIES,
    NLP_LIBRARIES,
    ORCHESTRATION_LIBRARIES,
    PHYSICS_LIBRARIES,
    POST_TRAINING_LIBRARIES,
    QUANTUM_COMPUTING_LIBRARIES,
    RAG_RETRIEVAL_LIBRARIES,
    RECOMMENDER_SYSTEMS_LIBRARIES,
    REINFORCEMENT_LEARNING_LIBRARIES,
    SAFETY_LIBRARIES,
    SIMULATION_LIBRARIES,
    SPATIAL_STATISTICS_LIBRARIES,
    STATISTICAL_ANALYSIS_LIBRARIES,
    STATISTICAL_ML_LIBRARIES,
    STRUCTURED_OUTPUT_LIBRARIES,
    SURVIVAL_ANALYSIS_LIBRARIES,
    TIME_SERIES_LIBRARIES,
    TOKENIZATION_LIBRARIES,
    VISION_LANGUAGE_LIBRARIES,
    VISION_LIBRARIES,
    VLA_LIBRARIES,
    WORLD_MODELS_LIBRARIES,
]

LIBRARY_DOCS: dict[str, dict[str, str | None]] = {}
for _registry in _CATEGORY_REGISTRIES:
    for _name, _entry in _registry.items():
        if _name in LIBRARY_DOCS:
            raise ValueError(f"Duplicate library name: {_name}")
        LIBRARY_DOCS[_name] = _entry
