# Orchestration (llm): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
ORCHESTRATION_LIBRARIES: dict[str, dict[str, str | None]] = {
    "langchain": {
        "description": "LLM application framework (chains, agents, integrations)",
        "domain": "llm",
        "category": "orchestration",
        "official_docs": "https://docs.langchain.com",
        "github": "https://github.com/langchain-ai/langchain",
        "llms_txt": "https://docs.langchain.com/llms.txt",
        "llms_full_txt": "https://docs.langchain.com/llms-full.txt",
    },
    "langgraph": {
        "description": "Stateful multi-actor LLM agent graphs",
        "domain": "llm",
        "category": "orchestration",
        "official_docs": "https://langchain-ai.github.io/langgraph",
        "github": "https://github.com/langchain-ai/langgraph",
        "llms_txt": "https://langchain-ai.github.io/langgraph/llms.txt",
        "llms_full_txt": None,
    },
    "litellm": {
        "description": "Unified API for 100+ LLM providers",
        "domain": "llm",
        "category": "orchestration",
        "official_docs": "https://docs.litellm.ai",
        "github": "https://github.com/BerriAI/litellm",
        "llms_txt": "https://docs.litellm.ai/llms.txt",
        "llms_full_txt": "https://docs.litellm.ai/llms-full.txt",
    },
}
