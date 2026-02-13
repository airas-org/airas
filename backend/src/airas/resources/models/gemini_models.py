GEMINI_MODELS = {
    # Gemini 3 Series (Preview)
    "gemini-3-pro-preview": {
        "model_parameters": "Unknown",  # TODO: Confirm final specs
        "model_architecture": "Multimodal transformer architecture",
        "training_data_sources": "Google proprietary training data",
        "api_provider": "Google Cloud Vertex AI / Google AI Studio",
        "model_id": "gemini-3-pro-preview",
        "task_type": "text-generation",
        "context_window": "Unknown",  # TODO: Confirm final specs
        "max_output_tokens": "Unknown",  # TODO: Confirm final specs
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image", "video", "audio"],
        "output_modalities": ["text"],
        "dependent_packages": ["google-genai"],
        "code": """\
# TODO: Confirm final specs - This is a preview model and specifications may change
from google import genai

client = genai.Client(api_key='YOUR_API_KEY')
response = client.models.generate_content(
    model='gemini-3-pro-preview',
    contents='Give me a short introduction to large language model.'
)
print(response.text)""",
        "citation": """\
@misc{google2025gemini3,
  title={Gemini 3 Model Preview},
  author={Google DeepMind},
  year={2025},
  note={Preview release - specifications subject to change}
}""",
    },
    "gemini-3-flash-preview": {
        "model_parameters": "Unknown",  # TODO: Confirm final specs
        "model_architecture": "Multimodal transformer architecture (optimized for speed)",
        "training_data_sources": "Google proprietary training data",
        "api_provider": "Google Cloud Vertex AI / Google AI Studio",
        "model_id": "gemini-3-flash-preview",
        "task_type": "text-generation",
        "context_window": "Unknown",  # TODO: Confirm final specs
        "max_output_tokens": "Unknown",  # TODO: Confirm final specs
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image", "video", "audio"],
        "output_modalities": ["text"],
        "dependent_packages": ["google-genai"],
        "code": """\
# TODO: Confirm final specs - This is a preview model and specifications may change
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
  note={Preview release - specifications subject to change}
}""",
    },
    # Gemini 2.5 Series
    "gemini-2.5-pro": {
        "model_parameters": "Unknown",
        "model_architecture": "Multimodal transformer architecture",
        "training_data_sources": "Google proprietary training data",
        "api_provider": "Google Cloud Vertex AI / Google AI Studio",
        "model_id": "gemini-2.5-pro",
        "task_type": "text-generation",
        "context_window": "2097152",  # 2M tokens based on Gemini 2.0 specifications
        "max_output_tokens": "8192",
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
        "model_parameters": "Unknown",
        "model_architecture": "Multimodal transformer architecture (optimized for speed)",
        "training_data_sources": "Google proprietary training data",
        "api_provider": "Google Cloud Vertex AI / Google AI Studio",
        "model_id": "gemini-2.5-flash",
        "task_type": "text-generation",
        "context_window": "1048576",  # 1M tokens based on Gemini 2.0 Flash specifications
        "max_output_tokens": "8192",
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
        "model_parameters": "Unknown",
        "model_architecture": "Multimodal transformer architecture (lightweight variant)",
        "training_data_sources": "Google proprietary training data",
        "api_provider": "Google Cloud Vertex AI / Google AI Studio",
        "model_id": "gemini-2.5-flash-lite",
        "task_type": "text-generation",
        "context_window": "1048576",  # Estimated based on Flash variant
        "max_output_tokens": "8192",
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
