# Curated model registry — language / hosted_api. Part of the shared
# domain>category taxonomy across resources/{libraries,models,datasets}.
# HuggingFace URLs and arXiv citations are verified on entry; use
# search_huggingface_hub for un-curated needs.
HOSTED_API_MODELS: dict = {
    "gemini-3-pro-preview": {
        "description": "",
        "model_parameters": "Unknown",
        "model_architecture": "Gemini model architecture with enhanced capabilities",
        "domain": "language",
        "category": "hosted_api",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/google/gemini-3-pro-preview",
        "dependent_packages": ["google-generativeai"],
        "code": """import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-3-pro-preview")
response = model.generate_content("Give me a short introduction to large language model.")
print(response.text)""",
        "citation": """@misc{google2025gemini3,
  title = {Gemini 3: Next Generation Multimodal AI},
  author = {Google DeepMind},
  year = {2025},
  url = {https://deepmind.google/technologies/gemini/}
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
    },
    "gemini-3-flash-preview": {
        "description": "",
        "model_parameters": "Unknown",
        "model_architecture": "Gemini model architecture optimized for speed",
        "domain": "language",
        "category": "hosted_api",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/google/gemini-3-flash-preview",
        "dependent_packages": ["google-generativeai"],
        "code": """import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-3-flash-preview")
response = model.generate_content("Give me a short introduction to large language model.")
print(response.text)""",
        "citation": """@misc{google2025gemini3,
  title = {Gemini 3: Next Generation Multimodal AI},
  author = {Google DeepMind},
  year = {2025},
  url = {https://deepmind.google/technologies/gemini/}
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
    },
    "gemini-2.5-pro": {
        "description": "",
        "model_parameters": "Unknown",
        "model_architecture": "Gemini 2.5 model architecture",
        "domain": "language",
        "category": "hosted_api",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/google/gemini-2.5-pro",
        "dependent_packages": ["google-generativeai"],
        "code": """import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-pro")
response = model.generate_content("Give me a short introduction to large language model.")
print(response.text)""",
        "citation": """@misc{google2025gemini25,
  title = {Gemini 2.5: Advanced Multimodal AI},
  author = {Google DeepMind},
  year = {2025},
  url = {https://deepmind.google/technologies/gemini/}
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
    },
    "gemini-2.5-flash": {
        "description": "",
        "model_parameters": "Unknown",
        "model_architecture": "Gemini 2.5 model architecture optimized for speed",
        "domain": "language",
        "category": "hosted_api",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/google/gemini-2.5-flash",
        "dependent_packages": ["google-generativeai"],
        "code": """import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")
response = model.generate_content("Give me a short introduction to large language model.")
print(response.text)""",
        "citation": """@misc{google2025gemini25,
  title = {Gemini 2.5: Advanced Multimodal AI},
  author = {Google DeepMind},
  year = {2025},
  url = {https://deepmind.google/technologies/gemini/}
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
    },
    "gemini-2.5-flash-lite": {
        "description": "",
        "model_parameters": "Unknown",
        "model_architecture": "Gemini 2.5 model architecture with lightweight optimizations",
        "domain": "language",
        "category": "hosted_api",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/google/gemini-2.5-flash-lite",
        "dependent_packages": ["google-generativeai"],
        "code": """import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-lite")
response = model.generate_content("Give me a short introduction to large language model.")
print(response.text)""",
        "citation": """@misc{google2025gemini25,
  title = {Gemini 2.5: Advanced Multimodal AI},
  author = {Google DeepMind},
  year = {2025},
  url = {https://deepmind.google/technologies/gemini/}
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
    },
}
