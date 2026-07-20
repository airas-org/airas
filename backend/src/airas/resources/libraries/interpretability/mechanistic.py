# interpretability / mechanistic documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
MECHANISTIC_LIBRARIES: dict[str, dict[str, str | None]] = {
    "transformerlens": {
        "description": "Mechanistic interpretability of GPT-style models (activation caching and patching)",
        "domain": "interpretability",
        "category": "mechanistic",
        "official_docs": "https://transformerlensorg.github.io/TransformerLens",
        "github": "https://github.com/TransformerLensOrg/TransformerLens",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "saelens": {
        "description": "Training and analyzing sparse autoencoders for interpretability",
        "domain": "interpretability",
        "category": "mechanistic",
        "official_docs": "https://decoderesearch.github.io/SAELens",
        "github": "https://github.com/decoderesearch/SAELens",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "nnsight": {
        "description": "Intervening on internals of arbitrary PyTorch models (including remote)",
        "domain": "interpretability",
        "category": "mechanistic",
        "official_docs": "https://nnsight.net",
        "github": "https://github.com/ndif-team/nnsight",
        "llms_txt": "https://nnsight.net/llms.txt",
        "llms_full_txt": None,
    },
    "pyvene": {
        "description": "Intervention-based interpretability experiments",
        "domain": "interpretability",
        "category": "mechanistic",
        "official_docs": "https://github.com/stanfordnlp/pyvene",
        "github": "https://github.com/stanfordnlp/pyvene",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
