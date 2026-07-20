# multimodal / vision_language documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
VISION_LANGUAGE_LIBRARIES: dict[str, dict[str, str | None]] = {
    "open-clip": {
        "description": "Open-source CLIP training and pretrained checkpoints",
        "domain": "multimodal",
        "category": "vision_language",
        "official_docs": "https://github.com/mlfoundations/open_clip",
        "github": "https://github.com/mlfoundations/open_clip",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "llava": {
        "description": "Large language-and-vision assistant (visual instruction tuning)",
        "domain": "multimodal",
        "category": "vision_language",
        "official_docs": "https://github.com/haotian-liu/LLaVA",
        "github": "https://github.com/haotian-liu/LLaVA",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "internvl": {
        "description": "Open multimodal foundation models (InternVL family)",
        "domain": "multimodal",
        "category": "vision_language",
        "official_docs": "https://internvl.readthedocs.io/en/latest",
        "github": "https://github.com/OpenGVLab/InternVL",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "lmms-eval": {
        "description": "Evaluation suite for large multimodal models",
        "domain": "multimodal",
        "category": "vision_language",
        "official_docs": "https://github.com/EvolvingLMMs-Lab/lmms-eval",
        "github": "https://github.com/EvolvingLMMs-Lab/lmms-eval",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
