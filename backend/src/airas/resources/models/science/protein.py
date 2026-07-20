# Curated model registry — science / protein. Part of the shared
# domain>category taxonomy across resources/{libraries,models,datasets}.
# HuggingFace URLs and arXiv citations are verified on entry; use
# search_huggingface_hub for un-curated needs.
PROTEIN_MODELS: dict = {
    "esm2-650m": {
        "description": "",
        "model_parameters": "652M",
        "model_architecture": "Protein language model over amino-acid sequences.",
        "domain": "science",
        "category": "protein",
        "task_type": "fill-mask",
        "huggingface_url": "https://huggingface.co/facebook/esm2_t33_650M_UR50D",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("fill-mask", model="facebook/esm2_t33_650M_UR50D")""",
        "citation": "",
        "training_data_sources": "",
    },
}
