LM_API_MODELS = {
    "gemini-3-pro-preview": {
        "model_parameters": "Unknown",
        "model_architecture": "Gemini model architecture with enhanced capabilities",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/google/gemini-3-pro-preview",
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "dependent_packages": ["google-generativeai"],
        "code": """\
import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-3-pro-preview")
response = model.generate_content("Give me a short introduction to large language model.")
print(response.text)""",
        "citation": """\
@misc{google2025gemini3,
  title = {Gemini 3: Next Generation Multimodal AI},
  author = {Google DeepMind},
  year = {2025},
  url = {https://deepmind.google/technologies/gemini/}
}""",
    },
    "gemini-3-flash-preview": {
        "model_parameters": "Unknown",
        "model_architecture": "Gemini model architecture optimized for speed",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/google/gemini-3-flash-preview",
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "dependent_packages": ["google-generativeai"],
        "code": """\
import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-3-flash-preview")
response = model.generate_content("Give me a short introduction to large language model.")
print(response.text)""",
        "citation": """\
@misc{google2025gemini3,
  title = {Gemini 3: Next Generation Multimodal AI},
  author = {Google DeepMind},
  year = {2025},
  url = {https://deepmind.google/technologies/gemini/}
}""",
    },
    "gemini-2.5-pro": {
        "model_parameters": "Unknown",
        "model_architecture": "Gemini 2.5 model architecture",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/google/gemini-2.5-pro",
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "dependent_packages": ["google-generativeai"],
        "code": """\
import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-pro")
response = model.generate_content("Give me a short introduction to large language model.")
print(response.text)""",
        "citation": """\
@misc{google2025gemini25,
  title = {Gemini 2.5: Advanced Multimodal AI},
  author = {Google DeepMind},
  year = {2025},
  url = {https://deepmind.google/technologies/gemini/}
}""",
    },
    "gemini-2.5-flash": {
        "model_parameters": "Unknown",
        "model_architecture": "Gemini 2.5 model architecture optimized for speed",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/google/gemini-2.5-flash",
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "dependent_packages": ["google-generativeai"],
        "code": """\
import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")
response = model.generate_content("Give me a short introduction to large language model.")
print(response.text)""",
        "citation": """\
@misc{google2025gemini25,
  title = {Gemini 2.5: Advanced Multimodal AI},
  author = {Google DeepMind},
  year = {2025},
  url = {https://deepmind.google/technologies/gemini/}
}""",
    },
    "gemini-2.5-flash-lite": {
        "model_parameters": "Unknown",
        "model_architecture": "Gemini 2.5 model architecture with lightweight optimizations",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/google/gemini-2.5-flash-lite",
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "dependent_packages": ["google-generativeai"],
        "code": """\
import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-lite")
response = model.generate_content("Give me a short introduction to large language model.")
print(response.text)""",
        "citation": """\
@misc{google2025gemini25,
  title = {Gemini 2.5: Advanced Multimodal AI},
  author = {Google DeepMind},
  year = {2025},
  url = {https://deepmind.google/technologies/gemini/}
}""",
    },
}
