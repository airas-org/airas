from enum import Enum
from typing import Annotated, TypeAlias, get_args

from pydantic import BaseModel, Field
from typing_extensions import Literal


class LLMProvider(str, Enum):
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    BEDROCK = "bedrock"


PROVIDER_REQUIRED_ENV_VARS: dict[LLMProvider, list[str]] = {
    LLMProvider.GOOGLE: [
        "GEMINI_API_KEY",
    ],
    LLMProvider.OPENAI: [
        "OPENAI_API_KEY",
    ],
    LLMProvider.ANTHROPIC: [
        "ANTHROPIC_API_KEY",
    ],
    LLMProvider.OPENROUTER: [
        "OPENROUTER_API_KEY",
    ],
    LLMProvider.BEDROCK: [
        "AWS_BEARER_TOKEN_BEDROCK",
    ],
}


# https://ai.google.dev/gemini-api/docs/models
GOOGLE_MODELS: TypeAlias = Literal[
    "gemini-3-pro-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-embedding-001",
]


# TODO: Add error handling for models that support thinking_config and validate thinking_budget ranges
# Currently supports gemini-2.5-pro with thinking_budget: 0 (off), 1024-32768 (fixed), -1 (dynamic)
class GoogleGenAIParams(BaseModel):
    provider_type: Literal["google_genai"] = "google_genai"
    thinking_budget: int | None = Field(
        None,
        description="Thinking budget for reasoning (0=off, 1024-32768=fixed, -1=dynamic)",
    )
    # Future extensions:
    # temperature: float | None = None
    # top_k: int | None = None
    # top_p: float | None = None


# https://platform.openai.com/docs/models
OPENAI_MODELS: TypeAlias = Literal[
    "gpt-5.2-pro-2025-12-11",
    "gpt-5.2-2025-12-11",
    "gpt-5.1-2025-11-13",
    "gpt-5-pro-2025-10-06",
    "gpt-5-codex",
    "gpt-5-2025-08-07",
    "gpt-5-mini-2025-08-07",
    "gpt-5-nano-2025-08-07",
    "gpt-4.1-2025-04-14",
    "gpt-4o-2024-11-20",
    "gpt-4o-mini-2024-07-18",
    "o4-mini-2025-04-16",
    "o3-2025-04-16",
    "o3-mini-2025-01-31",
    "o1-pro-2025-03-19",
    "o1-2024-12-17",
]

# TODO?: Add error handling for models that do not support reasoning effort
ReasoningEffort = Literal["none", "low", "medium", "high"]


class OpenAIParams(BaseModel):
    provider_type: Literal["openai"] = "openai"
    reasoning_effort: ReasoningEffort | None = Field(
        None, description="Reasoning effort level for reasoning models"
    )
    # Future extensions:
    # temperature: float | None = None
    # verbosity: Literal[...] | None = None


# https://platform.claude.com/docs/en/about-claude/models/overview
ANTHROPIC_MODELS: TypeAlias = Literal[
    "claude-opus-4-5",
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
    "claude-opus-4-1",
    "claude-opus-4",
    "claude-sonnet-4",
    "claude-3-7-sonnet",
    "claude-3-5-haiku",
]


class AnthropicParams(BaseModel):
    provider_type: Literal["anthropic"] = "anthropic"


ANTHROPIC_MODELS_FOR_OPENROUTER: TypeAlias = Literal[
    "anthropic/claude-opus-4.5",
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-haiku-4.5",
    "anthropic/claude-opus-4.1",
    "anthropic/claude-opus-4",
    "anthropic/claude-sonnet-4",
    "anthropic/claude-3.7-sonnet",
    "anthropic/claude-3.5-haiku",
]

OPENROUTER_MODELS: TypeAlias = Literal[
    *get_args(GOOGLE_MODELS),
    *get_args(OPENAI_MODELS),
    *get_args(ANTHROPIC_MODELS_FOR_OPENROUTER),
]

BEDROCK_MODELS = Literal[
    "anthropic.claude-opus-4-5-20251101-v1:0",
    "anthropic.claude-sonnet-4-5-20250929-v1:0",
    "anthropic.claude-haiku-4-5-20251001-v1:0",
    "anthropic.claude-sonnet-4-20250514-v1:0",
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "mistral.mistral-large-3-675b-instruct",  # Not support structured output
    "openai.gpt-oss-120b-1:0",  # Not support structured output
]


LLMParams = Annotated[
    OpenAIParams | GoogleGenAIParams | AnthropicParams,
    Field(discriminator="provider_type"),
]

LLM_MODELS: TypeAlias = (
    GOOGLE_MODELS
    | OPENAI_MODELS
    | ANTHROPIC_MODELS
    | OPENROUTER_MODELS
    | BEDROCK_MODELS
)
