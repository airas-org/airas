# Rag Retrieval (llm): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
RAG_RETRIEVAL_LIBRARIES: dict[str, dict[str, str | None]] = {
    "faiss": {
        "description": "Efficient similarity search and clustering of dense vectors",
        "domain": "llm",
        "category": "rag_retrieval",
        "official_docs": "https://faiss.ai",
        "github": "https://github.com/facebookresearch/faiss",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "sentence-transformers": {
        "description": "Sentence and text embeddings, rerankers",
        "domain": "llm",
        "category": "rag_retrieval",
        "official_docs": "https://www.sbert.net",
        "github": "https://github.com/huggingface/sentence-transformers",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "chromadb": {
        "description": "Open-source embedding database for RAG",
        "domain": "llm",
        "category": "rag_retrieval",
        "official_docs": "https://docs.trychroma.com",
        "github": "https://github.com/chroma-core/chroma",
        "llms_txt": "https://docs.trychroma.com/llms.txt",
        "llms_full_txt": "https://docs.trychroma.com/llms-full.txt",
    },
    "qdrant": {
        "description": "Vector database with filtering and hybrid search",
        "domain": "llm",
        "category": "rag_retrieval",
        "official_docs": "https://qdrant.tech/documentation",
        "github": "https://github.com/qdrant/qdrant",
        "llms_txt": "https://qdrant.tech/llms.txt",
        "llms_full_txt": "https://qdrant.tech/llms-full.txt",
    },
}
