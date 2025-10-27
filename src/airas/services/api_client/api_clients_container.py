from dependency_injector import containers, providers

from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.hugging_face_client import HuggingFaceClient
from airas.services.api_client.llm_client.anthropic_client import AnthropicClient
from airas.services.api_client.llm_client.google_genai_client import GoogleGenAIClient
from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.llm_client.openai_client import OpenAIClient
from airas.services.api_client.openalex_client import OpenAlexClient
from airas.services.api_client.semantic_scholar_client import SemanticScholarClient
from airas.services.api_client.wandb_client import WandbClient


class APIClientsContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    # --- LLM Clients ---
    openai_client = providers.Singleton(OpenAIClient)
    anthropic_client = providers.Singleton(AnthropicClient)
    google_genai_client = providers.Singleton(GoogleGenAIClient)

    llm_facade_client = providers.Factory(
        LLMFacadeClient,
        openai_client=openai_client,
        anthropic_client=anthropic_client,
        google_genai_client=google_genai_client,
    )

    # Delegate provider to inject the Factory itself
    # This allows passing runtime arguments (like llm_name) to the Factory
    llm_facade_provider = providers.Delegate(llm_facade_client)

    # --- Code & Experiment Platforms ---
    github_client = providers.Singleton(GithubClient)
    hugging_face_client = providers.Singleton(HuggingFaceClient)
    wandb_client = providers.Singleton(WandbClient)

    # --- Academic Research APIs ---
    arxiv_client = providers.Singleton(ArxivClient)
    semantic_scholar_client = providers.Singleton(SemanticScholarClient)
    openalex_client = providers.Singleton(OpenAlexClient)


api_clients_container = APIClientsContainer()
