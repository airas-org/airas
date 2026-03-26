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
