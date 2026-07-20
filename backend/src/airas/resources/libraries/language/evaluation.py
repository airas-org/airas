# language / evaluation documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
EVALUATION_LIBRARIES: dict[str, dict[str, str | None]] = {
    "lm-eval-harness": {
        "description": "Standard few-shot evaluation harness for language models",
        "domain": "language",
        "category": "evaluation",
        "official_docs": "https://github.com/EleutherAI/lm-evaluation-harness",
        "github": "https://github.com/EleutherAI/lm-evaluation-harness",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "lighteval": {
        "description": "Hugging Face LLM evaluation toolkit (multi-backend)",
        "domain": "language",
        "category": "evaluation",
        "official_docs": "https://huggingface.co/docs/lighteval",
        "github": "https://github.com/huggingface/lighteval",
        "llms_txt": "https://huggingface.co/docs/lighteval/llms.txt",
        "llms_full_txt": "https://huggingface.co/docs/lighteval/llms-full.txt",
    },
    "inspect-ai": {
        "description": "UK AISI framework for LLM safety and capability evaluations",
        "domain": "language",
        "category": "evaluation",
        "official_docs": "https://inspect.aisi.org.uk",
        "github": "https://github.com/UKGovernmentBEIS/inspect_ai",
        "llms_txt": "https://inspect.aisi.org.uk/llms.txt",
        "llms_full_txt": "https://inspect.aisi.org.uk/llms-full.txt",
    },
    "bigcode-evaluation-harness": {
        "description": "Code generation benchmark harness (HumanEval, MBPP, MultiPL-E)",
        "domain": "language",
        "category": "evaluation",
        "official_docs": "https://github.com/bigcode-project/bigcode-evaluation-harness",
        "github": "https://github.com/bigcode-project/bigcode-evaluation-harness",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
