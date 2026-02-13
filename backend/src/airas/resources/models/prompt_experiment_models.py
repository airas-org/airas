"""
Models specifically curated for prompt engineering experiments.

This module contains language models commonly used for prompt engineering experiments,
including both open-source transformer models and API-based models like Google's Gemini series.
"""

PROMPT_EXPERIMENT_MODELS = {
    # Gemini 3 Series (Preview)
    "gemini-3-pro-preview": {
        "model_parameters": "Large-scale (exact parameters undisclosed)",
        "model_architecture": "Multimodal transformer architecture with advanced reasoning capabilities",
        "training_data_sources": "Google proprietary training data",
        "api_provider": "Google Cloud Vertex AI / Google AI Studio",
        "model_id": "gemini-3-pro-preview",
        "task_type": "text-generation",
        "context_window": "1000000",  # 1M tokens
        "max_output_tokens": "65500",  # Up to 65,500 tokens
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image", "video", "audio"],
        "output_modalities": ["text"],
        "dependent_packages": ["google-genai"],
        "code": """\
from google import genai

client = genai.Client(api_key='YOUR_API_KEY')
response = client.models.generate_content(
    model='gemini-3-pro-preview',
    contents='Give me a short introduction to large language model.'
)
print(response.text)""",
        "citation": """\
@misc{google2025gemini3,
  title={Gemini 3: Introducing the latest Gemini AI model from Google},
  author={Google DeepMind},
  year={2025},
  url={https://blog.google/products-and-platforms/products/gemini/gemini-3/},
  note={Released November 18, 2025}
}""",
    },
    "gemini-3-flash-preview": {
        "model_parameters": "Large-scale (exact parameters undisclosed)",
        "model_architecture": "Multimodal transformer architecture (optimized for speed and efficiency)",
        "training_data_sources": "Google proprietary training data",
        "api_provider": "Google Cloud Vertex AI / Google AI Studio",
        "model_id": "gemini-3-flash-preview",
        "task_type": "text-generation",
        "context_window": "1000000",  # Estimated based on Gemini 3 series
        "max_output_tokens": "65500",  # Estimated based on Gemini 3 series
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image", "video", "audio"],
        "output_modalities": ["text"],
        "dependent_packages": ["google-genai"],
        "code": """\
from google import genai

client = genai.Client(api_key='YOUR_API_KEY')
response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='Give me a short introduction to large language model.'
)
print(response.text)""",
        "citation": """\
@misc{google2025gemini3flash,
  title={Gemini 3 Flash Model Preview},
  author={Google DeepMind},
  year={2025},
  note={Flash variant of Gemini 3 for faster processing}
}""",
    },
    # Gemini 2.5 Series
    "gemini-2.5-pro": {
        "model_parameters": "Large-scale (exact parameters undisclosed)",
        "model_architecture": "Multimodal transformer architecture",
        "training_data_sources": "Google proprietary training data",
        "api_provider": "Google Cloud Vertex AI / Google AI Studio",
        "model_id": "gemini-2.5-pro",
        "task_type": "text-generation",
        "context_window": "1000000",  # 1M tokens
        "max_output_tokens": "65000",  # Up to 65,000 tokens
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image", "video", "audio"],
        "output_modalities": ["text"],
        "dependent_packages": ["google-genai"],
        "code": """\
from google import genai

client = genai.Client(api_key='YOUR_API_KEY')
response = client.models.generate_content(
    model='gemini-2.5-pro',
    contents='Give me a short introduction to large language model.'
)
print(response.text)""",
        "citation": """\
@misc{google2025gemini25pro,
  title={Gemini 2.5 Pro},
  author={Google DeepMind},
  year={2025},
  url={https://ai.google.dev/gemini-api/docs/models/gemini}
}""",
    },
    "gemini-2.5-flash": {
        "model_parameters": "Large-scale (exact parameters undisclosed)",
        "model_architecture": "Multimodal transformer architecture (optimized for speed)",
        "training_data_sources": "Google proprietary training data",
        "api_provider": "Google Cloud Vertex AI / Google AI Studio",
        "model_id": "gemini-2.5-flash",
        "task_type": "text-generation",
        "context_window": "1048576",  # 1M tokens (1,048,576)
        "max_output_tokens": "65535",  # Up to 65,535 tokens
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image", "video", "audio"],
        "output_modalities": ["text"],
        "dependent_packages": ["google-genai"],
        "code": """\
from google import genai

client = genai.Client(api_key='YOUR_API_KEY')
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='Give me a short introduction to large language model.'
)
print(response.text)""",
        "citation": """\
@misc{google2025gemini25flash,
  title={Gemini 2.5 Flash},
  author={Google DeepMind},
  year={2025},
  url={https://ai.google.dev/gemini-api/docs/models/gemini}
}""",
    },
    "gemini-2.5-flash-lite": {
        "model_parameters": "Lightweight variant (exact parameters undisclosed)",
        "model_architecture": "Multimodal transformer architecture (lightweight variant)",
        "training_data_sources": "Google proprietary training data",
        "api_provider": "Google Cloud Vertex AI / Google AI Studio",
        "model_id": "gemini-2.5-flash-lite",
        "task_type": "text-generation",
        "context_window": "128000",  # 128K tokens for cost-optimized workloads
        "max_output_tokens": "8192",  # Lower output limit for efficiency
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "dependent_packages": ["google-genai"],
        "code": """\
from google import genai

client = genai.Client(api_key='YOUR_API_KEY')
response = client.models.generate_content(
    model='gemini-2.5-flash-lite',
    contents='Give me a short introduction to large language model.'
)
print(response.text)""",
        "citation": """\
@misc{google2025gemini25flashlite,
  title={Gemini 2.5 Flash Lite},
  author={Google DeepMind},
  year={2025},
  url={https://ai.google.dev/gemini-api/docs/models/gemini}
}""",
    },
}
