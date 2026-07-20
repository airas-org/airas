# Canonical documentation endpoints for libraries used in AI research,
# aggregated from one module per category (mirroring resources/models/).
# Instead of vendoring library documentation (which goes stale), agents
# fetch the living docs at experiment-code-writing time; `llms_txt` is
# the machine-readable entry point where the project publishes one
# (https://docs.nvidia.com/llms.txt is NVIDIA's site-wide index, used
# where no per-product llms.txt exists).
# To add a library: pick the category module (or create a new one and
# import it here), and verify every URL before adding — the weekly
# link-check workflow (check_library_docs_urls.yml) guards against rot.
from airas.resources.libraries.architecture_research import (
    ARCHITECTURE_RESEARCH_LIBRARIES,
)
from airas.resources.libraries.audio import AUDIO_LIBRARIES
from airas.resources.libraries.bayesian_inference import BAYESIAN_INFERENCE_LIBRARIES
from airas.resources.libraries.causal_inference import CAUSAL_INFERENCE_LIBRARIES
from airas.resources.libraries.classical_ml import CLASSICAL_ML_LIBRARIES
from airas.resources.libraries.core import CORE_LIBRARIES
from airas.resources.libraries.data_processing import DATA_PROCESSING_LIBRARIES
from airas.resources.libraries.distributed_training import (
    DISTRIBUTED_TRAINING_LIBRARIES,
)
from airas.resources.libraries.evaluation import EVALUATION_LIBRARIES
from airas.resources.libraries.experiment_tracking import EXPERIMENT_TRACKING_LIBRARIES
from airas.resources.libraries.fine_tuning import FINE_TUNING_LIBRARIES
from airas.resources.libraries.gpu_computing import GPU_COMPUTING_LIBRARIES
from airas.resources.libraries.graph_learning import GRAPH_LEARNING_LIBRARIES
from airas.resources.libraries.hyperparameter_optimization import (
    HYPERPARAMETER_OPTIMIZATION_LIBRARIES,
)
from airas.resources.libraries.inference_serving import INFERENCE_SERVING_LIBRARIES
from airas.resources.libraries.interpretability import INTERPRETABILITY_LIBRARIES
from airas.resources.libraries.jax_ecosystem import JAX_ECOSYSTEM_LIBRARIES
from airas.resources.libraries.llm_orchestration import LLM_ORCHESTRATION_LIBRARIES
from airas.resources.libraries.mathematical_optimization import (
    MATHEMATICAL_OPTIMIZATION_LIBRARIES,
)
from airas.resources.libraries.optimization import OPTIMIZATION_LIBRARIES
from airas.resources.libraries.post_training import POST_TRAINING_LIBRARIES
from airas.resources.libraries.quantum_computing import QUANTUM_COMPUTING_LIBRARIES
from airas.resources.libraries.rag_retrieval import RAG_RETRIEVAL_LIBRARIES
from airas.resources.libraries.reinforcement_learning import (
    REINFORCEMENT_LEARNING_LIBRARIES,
)
from airas.resources.libraries.safety import SAFETY_LIBRARIES
from airas.resources.libraries.scientific_ml import SCIENTIFIC_ML_LIBRARIES
from airas.resources.libraries.simulation import SIMULATION_LIBRARIES
from airas.resources.libraries.statistics import STATISTICS_LIBRARIES
from airas.resources.libraries.structured_output import STRUCTURED_OUTPUT_LIBRARIES
from airas.resources.libraries.time_series import TIME_SERIES_LIBRARIES
from airas.resources.libraries.tokenization import TOKENIZATION_LIBRARIES
from airas.resources.libraries.vision import VISION_LIBRARIES

_CATEGORY_REGISTRIES = [
    ARCHITECTURE_RESEARCH_LIBRARIES,
    AUDIO_LIBRARIES,
    BAYESIAN_INFERENCE_LIBRARIES,
    CAUSAL_INFERENCE_LIBRARIES,
    CLASSICAL_ML_LIBRARIES,
    CORE_LIBRARIES,
    DATA_PROCESSING_LIBRARIES,
    DISTRIBUTED_TRAINING_LIBRARIES,
    EVALUATION_LIBRARIES,
    EXPERIMENT_TRACKING_LIBRARIES,
    FINE_TUNING_LIBRARIES,
    GPU_COMPUTING_LIBRARIES,
    GRAPH_LEARNING_LIBRARIES,
    HYPERPARAMETER_OPTIMIZATION_LIBRARIES,
    INFERENCE_SERVING_LIBRARIES,
    INTERPRETABILITY_LIBRARIES,
    JAX_ECOSYSTEM_LIBRARIES,
    LLM_ORCHESTRATION_LIBRARIES,
    MATHEMATICAL_OPTIMIZATION_LIBRARIES,
    OPTIMIZATION_LIBRARIES,
    POST_TRAINING_LIBRARIES,
    QUANTUM_COMPUTING_LIBRARIES,
    RAG_RETRIEVAL_LIBRARIES,
    REINFORCEMENT_LEARNING_LIBRARIES,
    SAFETY_LIBRARIES,
    SCIENTIFIC_ML_LIBRARIES,
    SIMULATION_LIBRARIES,
    STATISTICS_LIBRARIES,
    STRUCTURED_OUTPUT_LIBRARIES,
    TIME_SERIES_LIBRARIES,
    TOKENIZATION_LIBRARIES,
    VISION_LIBRARIES,
]

LIBRARY_DOCS: dict[str, dict[str, str | None]] = {}
for _registry in _CATEGORY_REGISTRIES:
    for _name, _entry in _registry.items():
        if _name in LIBRARY_DOCS:
            raise ValueError(f"Duplicate library name: {_name}")
        LIBRARY_DOCS[_name] = _entry
