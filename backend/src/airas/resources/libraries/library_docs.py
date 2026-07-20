# Canonical documentation endpoints for libraries used in AI research,
# aggregated from a two-level domain/category tree (one module per
# category, mirroring the layout of resources/models/). Instead of
# vendoring library documentation (which goes stale), agents fetch the
# living docs at experiment-code-writing time; `llms_txt` is the
# machine-readable entry point where the project publishes one
# (https://docs.nvidia.com/llms.txt is NVIDIA's site-wide index, used
# where no per-product llms.txt exists).
# To add a library: edit the relevant domain/<category>.py (or add a new
# category module and import it below), verifying every URL first — the
# weekly link-check workflow (check_library_docs_urls.yml) guards rot.
from airas.resources.libraries.decision_science.decision_making import (
    DECISION_MAKING_LIBRARIES,
)
from airas.resources.libraries.decision_science.mathematical_optimization import (
    MATHEMATICAL_OPTIMIZATION_LIBRARIES,
)
from airas.resources.libraries.embodied_ai.reinforcement_learning import (
    REINFORCEMENT_LEARNING_LIBRARIES,
)
from airas.resources.libraries.embodied_ai.simulation import SIMULATION_LIBRARIES
from airas.resources.libraries.embodied_ai.vla import VLA_LIBRARIES
from airas.resources.libraries.embodied_ai.world_models import WORLD_MODELS_LIBRARIES
from airas.resources.libraries.foundations.core import CORE_LIBRARIES
from airas.resources.libraries.foundations.jax_ecosystem import JAX_ECOSYSTEM_LIBRARIES
from airas.resources.libraries.graphs.graph_learning import GRAPH_LEARNING_LIBRARIES
from airas.resources.libraries.graphs.network_analysis import NETWORK_ANALYSIS_LIBRARIES
from airas.resources.libraries.interpretability.explainable_ai import (
    EXPLAINABLE_AI_LIBRARIES,
)
from airas.resources.libraries.interpretability.mechanistic import MECHANISTIC_LIBRARIES
from airas.resources.libraries.llm.architecture_research import (
    ARCHITECTURE_RESEARCH_LIBRARIES,
)
from airas.resources.libraries.llm.evaluation import EVALUATION_LIBRARIES
from airas.resources.libraries.llm.fine_tuning import FINE_TUNING_LIBRARIES
from airas.resources.libraries.llm.nlp import NLP_LIBRARIES
from airas.resources.libraries.llm.orchestration import ORCHESTRATION_LIBRARIES
from airas.resources.libraries.llm.post_training import POST_TRAINING_LIBRARIES
from airas.resources.libraries.llm.rag_retrieval import RAG_RETRIEVAL_LIBRARIES
from airas.resources.libraries.llm.safety import SAFETY_LIBRARIES
from airas.resources.libraries.llm.structured_output import STRUCTURED_OUTPUT_LIBRARIES
from airas.resources.libraries.llm.tokenization import TOKENIZATION_LIBRARIES
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
from airas.resources.libraries.perception.audio import AUDIO_LIBRARIES
from airas.resources.libraries.perception.vision import VISION_LIBRARIES
from airas.resources.libraries.perception.vision_language import (
    VISION_LANGUAGE_LIBRARIES,
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
from airas.resources.libraries.statistics.time_series import TIME_SERIES_LIBRARIES
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

_CATEGORY_REGISTRIES = [
    CORE_LIBRARIES,
    JAX_ECOSYSTEM_LIBRARIES,
    FINE_TUNING_LIBRARIES,
    POST_TRAINING_LIBRARIES,
    ARCHITECTURE_RESEARCH_LIBRARIES,
    TOKENIZATION_LIBRARIES,
    EVALUATION_LIBRARIES,
    ORCHESTRATION_LIBRARIES,
    STRUCTURED_OUTPUT_LIBRARIES,
    RAG_RETRIEVAL_LIBRARIES,
    SAFETY_LIBRARIES,
    NLP_LIBRARIES,
    DISTRIBUTED_TRAINING_LIBRARIES,
    GPU_COMPUTING_LIBRARIES,
    INFERENCE_SERVING_LIBRARIES,
    MODEL_COMPRESSION_LIBRARIES,
    DATA_PROCESSING_LIBRARIES,
    EXPERIMENT_TRACKING_LIBRARIES,
    STATISTICAL_ANALYSIS_LIBRARIES,
    BAYESIAN_INFERENCE_LIBRARIES,
    SURVIVAL_ANALYSIS_LIBRARIES,
    EXPERIMENTAL_DESIGN_LIBRARIES,
    CAUSAL_INFERENCE_LIBRARIES,
    TIME_SERIES_LIBRARIES,
    SPATIAL_STATISTICS_LIBRARIES,
    STATISTICAL_ML_LIBRARIES,
    RECOMMENDER_SYSTEMS_LIBRARIES,
    ANOMALY_DETECTION_LIBRARIES,
    HYPERPARAMETER_OPTIMIZATION_LIBRARIES,
    MATHEMATICAL_OPTIMIZATION_LIBRARIES,
    DECISION_MAKING_LIBRARIES,
    REINFORCEMENT_LEARNING_LIBRARIES,
    SIMULATION_LIBRARIES,
    VLA_LIBRARIES,
    WORLD_MODELS_LIBRARIES,
    VISION_LIBRARIES,
    VISION_LANGUAGE_LIBRARIES,
    AUDIO_LIBRARIES,
    MECHANISTIC_LIBRARIES,
    EXPLAINABLE_AI_LIBRARIES,
    NETWORK_ANALYSIS_LIBRARIES,
    GRAPH_LEARNING_LIBRARIES,
    BIOINFORMATICS_LIBRARIES,
    MEDICAL_LIBRARIES,
    CHEMISTRY_MATERIALS_LIBRARIES,
    PHYSICS_LIBRARIES,
    QUANTUM_COMPUTING_LIBRARIES,
]

LIBRARY_DOCS: dict[str, dict[str, str | None]] = {}
for _registry in _CATEGORY_REGISTRIES:
    for _name, _entry in _registry.items():
        if _name in LIBRARY_DOCS:
            raise ValueError(f"Duplicate library name: {_name}")
        LIBRARY_DOCS[_name] = _entry
