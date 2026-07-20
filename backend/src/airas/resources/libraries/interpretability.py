# Interpretability libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
INTERPRETABILITY_LIBRARIES: dict[str, dict[str, str | None]] = {
    "transformerlens": {
        "description": "Mechanistic interpretability of GPT-style models (activation caching and patching)",
        "category": "interpretability",
        "official_docs": "https://transformerlensorg.github.io/TransformerLens",
        "github": "https://github.com/TransformerLensOrg/TransformerLens",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "saelens": {
        "description": "Training and analyzing sparse autoencoders for interpretability",
        "category": "interpretability",
        "official_docs": "https://decoderesearch.github.io/SAELens",
        "github": "https://github.com/decoderesearch/SAELens",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "nnsight": {
        "description": "Intervening on internals of arbitrary PyTorch models (including remote)",
        "category": "interpretability",
        "official_docs": "https://nnsight.net",
        "github": "https://github.com/ndif-team/nnsight",
        "llms_txt": "https://nnsight.net/llms.txt",
        "llms_full_txt": None,
    },
    "pyvene": {
        "description": "Intervention-based interpretability experiments",
        "category": "interpretability",
        "official_docs": "https://github.com/stanfordnlp/pyvene",
        "github": "https://github.com/stanfordnlp/pyvene",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "captum": {
        "description": "Model attribution and interpretability for PyTorch",
        "category": "interpretability",
        "official_docs": "https://captum.ai",
        "github": "https://github.com/meta-pytorch/captum",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
