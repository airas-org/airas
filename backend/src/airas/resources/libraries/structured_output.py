# Structured Output libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
STRUCTURED_OUTPUT_LIBRARIES: dict[str, dict[str, str | None]] = {
    "dspy": {
        "description": "Programming framework for LLM pipelines with automatic prompt optimization",
        "category": "structured_output",
        "official_docs": "https://dspy.ai",
        "github": "https://github.com/stanfordnlp/dspy",
        "llms_txt": "https://dspy.ai/llms.txt",
        "llms_full_txt": None,
    },
    "outlines": {
        "description": "Constrained generation for structured LLM output (JSON, regex, grammars)",
        "category": "structured_output",
        "official_docs": "https://dottxt-ai.github.io/outlines",
        "github": "https://github.com/dottxt-ai/outlines",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "instructor": {
        "description": "Structured LLM outputs validated with Pydantic",
        "category": "structured_output",
        "official_docs": "https://python.useinstructor.com",
        "github": "https://github.com/567-labs/instructor",
        "llms_txt": "https://python.useinstructor.com/llms.txt",
        "llms_full_txt": None,
    },
}
