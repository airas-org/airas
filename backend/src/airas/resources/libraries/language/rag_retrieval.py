# language / rag_retrieval documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
RAG_RETRIEVAL_LIBRARIES: dict[str, dict[str, str | None]] = {
    "faiss": {
        "description": "Efficient similarity search and clustering of dense vectors",
        "domain": "language",
        "category": "rag_retrieval",
        "official_docs": "https://faiss.ai",
        "github": "https://github.com/facebookresearch/faiss",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "sentence-transformers": {
        "description": "Sentence and text embeddings, rerankers",
        "domain": "language",
        "category": "rag_retrieval",
        "official_docs": "https://www.sbert.net",
        "github": "https://github.com/huggingface/sentence-transformers",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "chromadb": {
        "description": "Open-source embedding database for RAG",
        "domain": "language",
        "category": "rag_retrieval",
        "official_docs": "https://docs.trychroma.com",
        "github": "https://github.com/chroma-core/chroma",
        "llms_txt": "https://docs.trychroma.com/llms.txt",
        "llms_full_txt": "https://docs.trychroma.com/llms-full.txt",
    },
    "qdrant": {
        "description": "Vector database with filtering and hybrid search",
        "domain": "language",
        "category": "rag_retrieval",
        "official_docs": "https://qdrant.tech/documentation",
        "github": "https://github.com/qdrant/qdrant",
        "llms_txt": "https://qdrant.tech/llms.txt",
        "llms_full_txt": "https://qdrant.tech/llms-full.txt",
    },
}
