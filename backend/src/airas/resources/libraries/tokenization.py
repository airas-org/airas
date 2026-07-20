# Tokenization libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
TOKENIZATION_LIBRARIES: dict[str, dict[str, str | None]] = {
    "tokenizers": {
        "description": "Fast tokenizers (BPE, WordPiece, Unigram) with training support",
        "category": "tokenization",
        "official_docs": "https://huggingface.co/docs/tokenizers/main/en/index",
        "github": "https://github.com/huggingface/tokenizers",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "sentencepiece": {
        "description": "Language-independent subword tokenizer (BPE, unigram)",
        "category": "tokenization",
        "official_docs": "https://github.com/google/sentencepiece",
        "github": "https://github.com/google/sentencepiece",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "tiktoken": {
        "description": "Fast BPE tokenizer for OpenAI models",
        "category": "tokenization",
        "official_docs": "https://github.com/openai/tiktoken",
        "github": "https://github.com/openai/tiktoken",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
