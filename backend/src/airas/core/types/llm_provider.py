from enum import Enum


class LLMProvider(str, Enum):
    GOOGLE = "google"
    VERTEX_AI = "vertex_ai"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    BEDROCK = "bedrock"
    AZURE = "azure"
    VERCEL_AI_GATEWAY = "vercel_ai_gateway"
    # OpenAI-compatible endpoints, one provider per institution so keys stay
    # traceable to their host and billing. See OPENAI_COMPATIBLE_ENDPOINTS in
    # infra/llm_provider_resolver.py for how they are routed.
    RIKYU = "rikyu"
