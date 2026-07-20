# Curated model registry (see resources/models/registry.py for the
# subfield aggregation). HuggingFace URLs and arXiv citations are verified
# on entry; add candidates via search_huggingface_hub for un-curated needs.
PROTEIN_MODELS: dict = {
    "esm2-650m": {
        "model_parameters": "652M",
        "model_architecture": "Protein language model over amino-acid sequences.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/facebook/esm2_t33_650M_UR50D",
        "task_type": "fill-mask",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("fill-mask", model="facebook/esm2_t33_650M_UR50D")""",
        "citation": "",
    },
}
