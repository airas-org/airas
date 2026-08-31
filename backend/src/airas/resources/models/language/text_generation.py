# Curated model registry — language / text_generation. Part of the shared
# domain>category taxonomy across resources/{libraries,models,datasets}.
# HuggingFace URLs and arXiv citations are verified on entry; use
# search_huggingface_hub for un-curated needs.
TEXT_GENERATION_MODELS: dict = {
    "Llama-4-Scout-17B-16E": {
        "description": "",
        "model_parameters": {"total_parameters": "109b", "active_parameters": "17b"},
        "model_architecture": "Transformer-based Mixture-of-Experts (MoE) architecture",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E",
        "dependent_packages": [],
        "code": """from transformers import pipeline
model_id = "meta-llama/Llama-4-Scout-17B-16E"
pipe = pipeline(
    "text-generation",
    model=model_id,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)
prompt = "Give me a short introduction to large language model."
output = pipe(prompt, max_new_tokens=150)
print(output)""",
        "citation": """@misc{meta2024llama4,
  title = {Introducing LLaMA 4: Advancing Multimodal Intelligence},
  author = {Meta AI},
  year = {2024},
  url = {https://ai.meta.com/blog/llama-4-multimodal-intelligence/}
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
    },
    "Llama-4-Maverick-17B-128E": {
        "description": "",
        "model_parameters": {"total_parameters": "400b", "active_parameters": "17b"},
        "model_architecture": "Transformer-based Mixture-of-Experts (MoE) architecture",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E",
        "dependent_packages": [],
        "code": """from transformers import pipeline
model_id = "meta-llama/Llama-4-Maverick-17B-128E"
pipe = pipeline(
    "text-generation",
    model=model_id,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)
prompt = "Give me a short introduction to large language model."
output = pipe(prompt, max_new_tokens=150)
print(output)""",
        "citation": """@misc{meta2024llama4,
  title = {Introducing LLaMA 4: Advancing Multimodal Intelligence},
  author = {Meta AI},
  year = {2024},
  url = {https://ai.meta.com/blog/llama-4-multimodal-intelligence/}
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
    },
    "Qwen3-0.6B": {
        "description": "",
        "model_parameters": "0.6b",
        "model_architecture": "Transformer",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/Qwen/Qwen3-0.6B",
        "dependent_packages": ["transformers>=4.51.0"],
        "code": """from transformers import AutoModelForCausalLM, AutoTokenizer
model_name = "Qwen/Qwen3-0.6B"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
model_name,
torch_dtype="auto",
device_map="auto"
)

prompt = "Give me a short introduction to large language model."
messages = [
{"role": "user", "content": prompt}
]
text = tokenizer.apply_chat_template(
messages,
tokenize=False,
add_generation_prompt=True,
enable_thinking=True # Switches between thinking and non-thinking modes. Default is True.
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

generated_ids = model.generate(
**model_inputs,
max_new_tokens=32768
)
output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()""",
        "citation": """@misc{qwen3technicalreport,
    title={Qwen3 Technical Report},
    author={Qwen Team},
    year={2025},
    eprint={2505.09388},
    archivePrefix={arXiv},
    primaryClass={cs.CL},
    url={https://arxiv.org/abs/2505.09388},
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
    },
    "Qwen3-1.7B": {
        "description": "",
        "model_parameters": "1.7b",
        "model_architecture": "Transformer",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/Qwen/Qwen3-1.7B",
        "dependent_packages": ["transformers>=4.51.0"],
        "code": """from transformers import AutoModelForCausalLM, AutoTokenizer
model_name = "Qwen/Qwen3-1.7B"

# load the tokenizer and the model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
model_name,
torch_dtype="auto",
device_map="auto"
)

# prepare the model input
prompt = "Give me a short introduction to large language model."
messages = [
{"role": "user", "content": prompt}
]
text = tokenizer.apply_chat_template(
messages,
tokenize=False,
add_generation_prompt=True,
enable_thinking=True # Switches between thinking and non-thinking modes. Default is True.
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

# conduct text completion
generated_ids = model.generate(
**model_inputs,
max_new_tokens=32768
)
output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()""",
        "citation": """@misc{qwen3technicalreport,
    title={Qwen3 Technical Report},
    author={Qwen Team},
    year={2025},
    eprint={2505.09388},
    archivePrefix={arXiv},
    primaryClass={cs.CL},
    url={https://arxiv.org/abs/2505.09388},
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
    },
    "Qwen3-4B": {
        "description": "",
        "model_parameters": "4b",
        "model_architecture": "Transformer",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/Qwen/Qwen3-4B",
        "dependent_packages": ["transformers>=4.51.0"],
        "code": """from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen3-4B"

# load the tokenizer and the model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
model_name,
torch_dtype="auto",
device_map="auto"
)

# prepare the model input
prompt = "Give me a short introduction to large language model."
messages = [
{"role": "user", "content": prompt}
]
text = tokenizer.apply_chat_template(
messages,
tokenize=False,
add_generation_prompt=True,
enable_thinking=True # Switches between thinking and non-thinking modes. Default is True.
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

# conduct text completion
generated_ids = model.generate(
**model_inputs,
max_new_tokens=32768
)
output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()""",
        "citation": """@misc{qwen3technicalreport,
    title={Qwen3 Technical Report},
    author={Qwen Team},
    year={2025},
    eprint={2505.09388},
    archivePrefix={arXiv},
    primaryClass={cs.CL},
    url={https://arxiv.org/abs/2505.09388},
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
    },
    "Qwen3-8B": {
        "description": "",
        "model_parameters": "8b",
        "model_architecture": "Transformer",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/Qwen/Qwen3-8B",
        "dependent_packages": ["transformers>=4.51.0"],
        "code": """from transformers import AutoModelForCausalLM, AutoTokenizer
model_name = "Qwen/Qwen3-8B"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
model_name,
torch_dtype="auto",
device_map="auto"
)

prompt = "Give me a short introduction to large language model."
messages = [
{"role": "user", "content": prompt}
]
text = tokenizer.apply_chat_template(
messages,
tokenize=False,
add_generation_prompt=True,
enable_thinking=True # Switches between thinking and non-thinking modes. Default is True.
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

generated_ids = model.generate(
**model_inputs,
max_new_tokens=32768
)
output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()""",
        "citation": """@misc{qwen3technicalreport,
    title={Qwen3 Technical Report},
    author={Qwen Team},
    year={2025},
    eprint={2505.09388},
    archivePrefix={arXiv},
    primaryClass={cs.CL},
    url={https://arxiv.org/abs/2505.09388},
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
    },
    "Qwen3-14B": {
        "description": "",
        "model_parameters": "14b",
        "model_architecture": "Transformer",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/Qwen/Qwen3-14B",
        "dependent_packages": ["transformers>=4.51.0"],
        "code": """from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen3-14B"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
model_name,
torch_dtype="auto",
device_map="auto"
)

prompt = "Give me a short introduction to large language model."
messages = [
{"role": "user", "content": prompt}
]
text = tokenizer.apply_chat_template(
messages,
tokenize=False,
add_generation_prompt=True,
enable_thinking=True # Switches between thinking and non-thinking modes. Default is True.
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

generated_ids = model.generate(
**model_inputs,
max_new_tokens=32768
)
output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()""",
        "citation": """@misc{qwen3technicalreport,
    title={Qwen3 Technical Report},
    author={Qwen Team},
    year={2025},
    eprint={2505.09388},
    archivePrefix={arXiv},
    primaryClass={cs.CL},
    url={https://arxiv.org/abs/2505.09388},
}""",
        "training_data_sources": "",
        "language_distribution": "",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
    },
    "Qwen3-32B": {
        "description": "",
        "model_parameters": "32.8b",
        "model_architecture": "Transformer",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/Qwen/Qwen3-32B",
        "dependent_packages": ["transformers>=4.51.0"],
        "code": """from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen3-32B"

# load the tokenizer and the model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
model_name,
torch_dtype="auto",
device_map="auto"
)

# prepare the model input
prompt = "Give me a short introduction to large language model."
messages = [
{"role": "user", "content": prompt}
]
text = tokenizer.apply_chat_template(
messages,
tokenize=False,
add_generation_prompt=True,
enable_thinking=True # Switches between thinking and non-thinking modes. Default is True.
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

# conduct text completion
generated_ids = model.generate(
**model_inputs,
max_new_tokens=32768
)
output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()""",
        "citation": """@misc{qwen3technicalreport,
    title={Qwen3 Technical Report},
    author={Qwen Team},
    year={2025},
    eprint={2505.09388},
    archivePrefix={arXiv},
    primaryClass={cs.CL},
    url={https://arxiv.org/abs/2505.09388},
}""",
        "training_data_sources": "",
        "language_distribution": "",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
    },
    "DeepSeek-v3": {
        "description": "",
        "model_parameters": {"total_parameters": "671b", "active_parameters": "37b"},
        "model_architecture": "Transformer-based Mixture-of-Experts (MoE) architecture",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/deepseek-ai/DeepSeek-V3",
        "dependent_packages": [],
        "code": "",
        "citation": """@misc{deepseekai2024deepseekv3technicalreport,
    title={DeepSeek-V3 Technical Report},
    author={DeepSeek-AI},
    year={2024},
    eprint={2412.19437},
    archivePrefix={arXiv},
    primaryClass={cs.CL},
    url={https://arxiv.org/abs/2412.19437},
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
    },
    "DeepSeek-V3.1": {
        "description": "",
        "model_parameters": {"total_parameters": "671B", "active_parameters": "37B"},
        "model_architecture": "Transformer-based Mixture-of-Experts (MoE) architecture",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/deepseek-ai/DeepSeek-V3.1",
        "dependent_packages": [],
        "code": "",
        "citation": """@misc{deepseekai2024deepseekv3technicalreport,
    title={DeepSeek-V3 Technical Report},
    author={DeepSeek-AI},
    year={2024},
    eprint={2412.19437},
    archivePrefix={arXiv},
    primaryClass={cs.CL},
    url={https://arxiv.org/abs/2412.19437},
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
    },
    "DeepSeek-V3.2-Exp": {
        "description": "",
        "model_parameters": {"total_parameters": "671B", "active_parameters": "37B"},
        "model_architecture": "Transformer-based Mixture-of-Experts (MoE) architecture",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/deepseek-ai/DeepSeek-V3.2-Exp",
        "dependent_packages": [],
        "code": "",
        "citation": """@misc{deepseekai2024deepseekv32,
    title={DeepSeek-V3.2-Exp: Boosting Long-Context Efficiency with DeepSeek Sparse Attention},
    author={DeepSeek-AI},
    year={2025},
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
    },
    "gpt-oss-20b": {
        "description": "",
        "model_parameters": {"total_parameters": "21b", "active_parameters": "3.6b"},
        "model_architecture": "Transformer-based Mixture-of-Experts (MoE) architecture",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/openai/gpt-oss-20b",
        "dependent_packages": ["accelerate", "transformers", "kernels"],
        "code": """from transformers import AutoModelForCausalLM, AutoTokenizer
model_id = "openai/gpt-oss-20b"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
model_id,
device_map="auto",
torch_dtype="auto",
)
messages = [
{"role": "user", "content": "How many rs are in the word 'strawberry'?"},
]

inputs = tokenizer.apply_chat_template(
messages,
add_generation_prompt=True,
return_tensors="pt",
return_dict=True,
).to(model.device)

generated = model.generate(**inputs, max_new_tokens=100)
print(tokenizer.decode(generated[0][inputs["input_ids"].shape[-1]:]))
""",
        "citation": """@misc{openai2025gptoss120bgptoss20bmodel,
    title={gpt-oss-120b & gpt-oss-20b Model Card},
    author={OpenAI},
    year={2025},
    eprint={2508.10925},
    archivePrefix={arXiv},
    primaryClass={cs.CL},
    url={https://arxiv.org/abs/2508.10925},
}""",
        "training_data_sources": "",
        "context_length": "",
        "language_distribution": "multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
    },
    "gemma-3-1b-it": {
        "description": "",
        "model_parameters": "1b",
        "model_architecture": "Transformer",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/google/gemma-3-1b-it",
        "dependent_packages": ["transformers"],
        "code": """from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("google/gemma-3-1b-it")
model = AutoModelForCausalLM.from_pretrained("google/gemma-3-1b-it")
messages = [
{"role": "user", "content": "自己紹介してください"},
]
inputs = tokenizer.apply_chat_template(
messages,
add_generation_prompt=True,
tokenize=True,
return_dict=True,
return_tensors="pt",
).to(model.device)

outputs = model.generate(**inputs, max_new_tokens=4000)
print(tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:]))
""",
        "citation": """@article{gemma_2025,
title={Gemma 3},
url={https://goo.gle/Gemma3Report},
publisher={Kaggle},
author={Gemma Team},
year={2025}
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
    },
    "gemma-3-4b-it": {
        "description": "",
        "model_parameters": "4b",
        "model_architecture": "Transformer",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/google/gemma-3-4b-it",
        "dependent_packages": ["transformers"],
        "code": """from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("google/gemma-3-4b-it")
model = AutoModelForCausalLM.from_pretrained("google/gemma-3-4b-it")
messages = [
{"role": "user", "content": "自己紹介してください"},
]
inputs = tokenizer.apply_chat_template(
messages,
add_generation_prompt=True,
tokenize=True,
return_dict=True,
return_tensors="pt",
).to(model.device)

outputs = model.generate(**inputs, max_new_tokens=4000)
print(tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:]))
""",
        "citation": """@article{gemma_2025,
title={Gemma 3},
url={https://goo.gle/Gemma3Report},
publisher={Kaggle},
author={Gemma Team},
year={2025}
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
    },
    "gemma-3-27b-it": {
        "description": "",
        "model_parameters": "27b",
        "model_architecture": "Transformer",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/google/gemma-3-27b-it",
        "dependent_packages": ["transformers"],
        "code": """from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("google/gemma-3-27b-it")
model = AutoModelForCausalLM.from_pretrained("google/gemma-3-27b-it")
messages = [
{"role": "user", "content": "自己紹介してください"},
]
inputs = tokenizer.apply_chat_template(
messages,
add_generation_prompt=True,
tokenize=True,
return_dict=True,
return_tensors="pt",
).to(model.device)

outputs = model.generate(**inputs, max_new_tokens=4000)
print(tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:]))
""",
        "citation": """@article{gemma_2025,
title={Gemma 3},
url={https://goo.gle/Gemma3Report},
publisher={Kaggle},
author={Gemma Team},
year={2025}
}""",
        "training_data_sources": "",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
    },
    "Mistral-7B-v0.3": {
        "description": "",
        "model_parameters": "7.3B",
        "model_architecture": "Transformer decoder with Grouped-Query Attention (GQA), Sliding-Window Attention, Byte-fallback BPE tokenizer, extended vocabulary to 32,768 tokens",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/mistralai/Mistral-7B-v0.3",
        "dependent_packages": [
            "transformers",
            "torch",
            "mistral-inference (recommended)",
            "huggingface-hub",
        ],
        "code": """from transformers import AutoModelForCausalLM, AutoTokenizer
model_id = "mistralai/Mistral-7B-v0.3"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)

inputs = tokenizer("Hello my name is", return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=20)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))""",
        "citation": "@article{jiang2023mistral, title={Mistral 7B}, author={Albert Q. Jiang and Alexandre Sablayrolles and Arthur Mensch and others}, journal={arXiv preprint arXiv:2310.06825}, year={2023}}",
        "training_data_sources": "Large-scale web data (proprietary, not publicly disclosed in detail)",
        "language_distribution": "Primarily English (multilingual capabilities present)",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
    },
    "mistral-7b-v0.3": {
        "description": "",
        "model_parameters": "7.2B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/mistralai/Mistral-7B-v0.3",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="mistralai/Mistral-7B-v0.3")""",
        "citation": """@misc{jiang2023,
  title = {Mistral 7B},
  author = {Albert Q. Jiang and Alexandre Sablayrolles and Arthur Mensch and Chris Bamford and Devendra Singh Chaplot and Diego de las Casas and Florian Bressand and Gianna Lengyel and Guillaume Lample and Lucile Saulnier and Lélio Renard Lavaud and Marie-Anne Lachaux and Pierre Stock and Teven Le Scao and Thibaut Lavril and Thomas Wang and Timothée Lacroix and William El Sayed},
  year = {2023},
  eprint = {2310.06825},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2310.06825}
}""",
        "training_data_sources": "",
    },
    "phi-3-mini-4k-instruct": {
        "description": "",
        "model_parameters": "3.8B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="microsoft/Phi-3-mini-4k-instruct")""",
        "citation": """@misc{abdin2024,
  title = {Phi-3 Technical Report: A Highly Capable Language Model Locally on Your Phone},
  author = {Marah Abdin and Jyoti Aneja and Hany Awadalla and Ahmed Awadallah and Ammar Ahmad Awan and Nguyen Bach and Amit Bahree and Arash Bakhtiari and Jianmin Bao and Harkirat Behl and Alon Benhaim and Misha Bilenko and Johan Bjorck and Sébastien Bubeck and Martin Cai and Qin Cai and Vishrav Chaudhary and Dong Chen and Dongdong Chen and Weizhu Chen and Yen-Chun Chen and Yi-Ling Chen and Hao Cheng and Parul Chopra and Xiyang Dai and Matthew Dixon and Ronen Eldan and Victor Fragoso and Jianfeng Gao and Mei Gao and Min Gao and Amit Garg and Allie Del Giorno and Abhishek Goswami and Suriya Gunasekar and Emman Haider and Junheng Hao and Russell J. Hewett and Wenxiang Hu and Jamie Huynh and Dan Iter and Sam Ade Jacobs and Mojan Javaheripi and Xin Jin and Nikos Karampatziakis and Piero Kauffmann and Mahoud Khademi and Dongwoo Kim and Young Jin Kim and Lev Kurilenko and James R. Lee and Yin Tat Lee and Yuanzhi Li and Yunsheng Li and Chen Liang and Lars Liden and Xihui Lin and Zeqi Lin and Ce Liu and Liyuan Liu and Mengchen Liu and Weishung Liu and Xiaodong Liu and Chong Luo and Piyush Madan and Ali Mahmoudzadeh and David Majercak and Matt Mazzola and Caio César Teodoro Mendes and Arindam Mitra and Hardik Modi and Anh Nguyen and Brandon Norick and Barun Patra and Daniel Perez-Becker and Thomas Portet and Reid Pryzant and Heyang Qin and Marko Radmilac and Liliang Ren and Gustavo de Rosa and Corby Rosset and Sambudha Roy and Olatunji Ruwase and Olli Saarikivi and Amin Saied and Adil Salim and Michael Santacroce and Shital Shah and Ning Shang and Hiteshi Sharma and Yelong Shen and Swadheen Shukla and Xia Song and Masahiro Tanaka and Andrea Tupini and Praneetha Vaddamanu and Chunyu Wang and Guanhua Wang and Lijuan Wang and Shuohang Wang and Xin Wang and Yu Wang and Rachel Ward and Wen Wen and Philipp Witte and Haiping Wu and Xiaoxia Wu and Michael Wyatt and Bin Xiao and Can Xu and Jiahang Xu and Weijian Xu and Jilong Xue and Sonali Yadav and Fan Yang and Jianwei Yang and Yifan Yang and Ziyi Yang and Donghan Yu and Lu Yuan and Chenruidong Zhang and Cyril Zhang and Jianwen Zhang and Li Lyna Zhang and Yi Zhang and Yue Zhang and Yunan Zhang and Xiren Zhou},
  year = {2024},
  eprint = {2404.14219},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2404.14219}
}""",
        "training_data_sources": "",
    },
    "falcon-7b": {
        "description": "",
        "model_parameters": "7.2B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/tiiuae/falcon-7b",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="tiiuae/falcon-7b")""",
        "citation": """@misc{almazrouei2023,
  title = {The Falcon Series of Open Language Models},
  author = {Ebtesam Almazrouei and Hamza Alobeidli and Abdulaziz Alshamsi and Alessandro Cappelli and Ruxandra Cojocaru and Mérouane Debbah and Étienne Goffinet and Daniel Hesslow and Julien Launay and Quentin Malartic and Daniele Mazzotta and Badreddine Noune and Baptiste Pannier and Guilherme Penedo},
  year = {2023},
  eprint = {2311.16867},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2311.16867}
}""",
        "training_data_sources": "",
    },
    "pythia-1.4b": {
        "description": "",
        "model_parameters": "1.5B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/EleutherAI/pythia-1.4b",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="EleutherAI/pythia-1.4b")""",
        "citation": """@misc{biderman2023,
  title = {Pythia: A Suite for Analyzing Large Language Models Across Training and Scaling},
  author = {Stella Biderman and Hailey Schoelkopf and Quentin Anthony and Herbie Bradley and Kyle O'Brien and Eric Hallahan and Mohammad Aflah Khan and Shivanshu Purohit and USVSN Sai Prashanth and Edward Raff and Aviya Skowron and Lintang Sutawika and Oskar van der Wal},
  year = {2023},
  eprint = {2304.01373},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2304.01373}
}""",
        "training_data_sources": "",
    },
    "olmo-2-1124-7b": {
        "description": "",
        "model_parameters": "7.3B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/allenai/OLMo-2-1124-7B",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="allenai/OLMo-2-1124-7B")""",
        "citation": """@misc{olmo2024,
  title = {2 OLMo 2 Furious},
  author = {Team OLMo and Pete Walsh and Luca Soldaini and Dirk Groeneveld and Kyle Lo and Shane Arora and Akshita Bhagia and Yuling Gu and Shengyi Huang and Matt Jordan and Nathan Lambert and Dustin Schwenk and Oyvind Tafjord and Taira Anderson and David Atkinson and Faeze Brahman and Christopher Clark and Pradeep Dasigi and Nouha Dziri and Allyson Ettinger and Michal Guerquin and David Heineman and Hamish Ivison and Pang Wei Koh and Jiacheng Liu and Saumya Malik and William Merrill and Lester James V. Miranda and Jacob Morrison and Tyler Murray and Crystal Nam and Jake Poznanski and Valentina Pyatkin and Aman Rangapur and Michael Schmitz and Sam Skjonsberg and David Wadden and Christopher Wilhelm and Michael Wilson and Luke Zettlemoyer and Ali Farhadi and Noah A. Smith and Hannaneh Hajishirzi},
  year = {2024},
  eprint = {2501.00656},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2501.00656}
}""",
        "training_data_sources": "",
    },
    "smollm2-1.7b": {
        "description": "",
        "model_parameters": "1.7B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="HuggingFaceTB/SmolLM2-1.7B")""",
        "citation": """@misc{allal2025,
  title = {SmolLM2: When Smol Goes Big -- Data-Centric Training of a Small Language Model},
  author = {Loubna Ben Allal and Anton Lozhkov and Elie Bakouch and Gabriel Martín Blázquez and Guilherme Penedo and Lewis Tunstall and Andrés Marafioti and Hynek Kydlíček and Agustín Piqueres Lajarín and Vaibhav Srivastav and Joshua Lochner and Caleb Fahlgren and Xuan-Son Nguyen and Clémentine Fourrier and Ben Burtenshaw and Hugo Larcher and Haojun Zhao and Cyril Zakka and Mathieu Morlon and Colin Raffel and Leandro von Werra and Thomas Wolf},
  year = {2025},
  eprint = {2502.02737},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2502.02737}
}""",
        "training_data_sources": "",
    },
    "qwen2.5-7b": {
        "description": "",
        "model_parameters": "7.6B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/Qwen/Qwen2.5-7B",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="Qwen/Qwen2.5-7B")""",
        "citation": """@misc{qwen2024,
  title = {Qwen2.5 Technical Report},
  author = { Qwen and  : and An Yang and Baosong Yang and Beichen Zhang and Binyuan Hui and Bo Zheng and Bowen Yu and Chengyuan Li and Dayiheng Liu and Fei Huang and Haoran Wei and Huan Lin and Jian Yang and Jianhong Tu and Jianwei Zhang and Jianxin Yang and Jiaxi Yang and Jingren Zhou and Junyang Lin and Kai Dang and Keming Lu and Keqin Bao and Kexin Yang and Le Yu and Mei Li and Mingfeng Xue and Pei Zhang and Qin Zhu and Rui Men and Runji Lin and Tianhao Li and Tianyi Tang and Tingyu Xia and Xingzhang Ren and Xuancheng Ren and Yang Fan and Yang Su and Yichang Zhang and Yu Wan and Yuqiong Liu and Zeyu Cui and Zhenru Zhang and Zihan Qiu},
  year = {2024},
  eprint = {2412.15115},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2412.15115}
}""",
        "training_data_sources": "",
    },
    "opt-1.3b": {
        "description": "",
        "model_parameters": "Unknown",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/facebook/opt-1.3b",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="facebook/opt-1.3b")""",
        "citation": """@misc{zhang2022,
  title = {OPT: Open Pre-trained Transformer Language Models},
  author = {Susan Zhang and Stephen Roller and Naman Goyal and Mikel Artetxe and Moya Chen and Shuohui Chen and Christopher Dewan and Mona Diab and Xian Li and Xi Victoria Lin and Todor Mihaylov and Myle Ott and Sam Shleifer and Kurt Shuster and Daniel Simig and Punit Singh Koura and Anjali Sridhar and Tianlu Wang and Luke Zettlemoyer},
  year = {2022},
  eprint = {2205.01068},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2205.01068}
}""",
        "training_data_sources": "",
    },
    "bloom-1b7": {
        "description": "",
        "model_parameters": "1.7B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/bigscience/bloom-1b7",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="bigscience/bloom-1b7")""",
        "citation": """@misc{workshop2022,
  title = {BLOOM: A 176B-Parameter Open-Access Multilingual Language Model},
  author = {BigScience Workshop and  : and Teven Le Scao and Angela Fan and Christopher Akiki and Ellie Pavlick and Suzana Ilić and Daniel Hesslow and Roman Castagné and Alexandra Sasha Luccioni and François Yvon and Matthias Gallé and Jonathan Tow and Alexander M. Rush and Stella Biderman and Albert Webson and Pawan Sasanka Ammanamanchi and Thomas Wang and Benoît Sagot and Niklas Muennighoff and Albert Villanova del Moral and Olatunji Ruwase and Rachel Bawden and Stas Bekman and Angelina McMillan-Major and Iz Beltagy and Huu Nguyen and Lucile Saulnier and Samson Tan and Pedro Ortiz Suarez and Victor Sanh and Hugo Laurençon and Yacine Jernite and Julien Launay and Margaret Mitchell and Colin Raffel and Aaron Gokaslan and Adi Simhi and Aitor Soroa and Alham Fikri Aji and Amit Alfassy and Anna Rogers and Ariel Kreisberg Nitzav and Canwen Xu and Chenghao Mou and Chris Emezue and Christopher Klamm and Colin Leong and Daniel van Strien and David Ifeoluwa Adelani and Dragomir Radev and Eduardo González Ponferrada and Efrat Levkovizh and Ethan Kim and Eyal Bar Natan and Francesco De Toni and Gérard Dupont and Germán Kruszewski and Giada Pistilli and Hady Elsahar and Hamza Benyamina and Hieu Tran and Ian Yu and Idris Abdulmumin and Isaac Johnson and Itziar Gonzalez-Dios and Javier de la Rosa and Jenny Chim and Jesse Dodge and Jian Zhu and Jonathan Chang and Jörg Frohberg and Joseph Tobing and Joydeep Bhattacharjee and Khalid Almubarak and Kimbo Chen and Kyle Lo and Leandro Von Werra and Leon Weber and Long Phan and Loubna Ben allal and Ludovic Tanguy and Manan Dey and Manuel Romero Muñoz and Maraim Masoud and María Grandury and Mario Šaško and Max Huang and Maximin Coavoux and Mayank Singh and Mike Tian-Jian Jiang and Minh Chien Vu and Mohammad A. Jauhar and Mustafa Ghaleb and Nishant Subramani and Nora Kassner and Nurulaqilla Khamis and Olivier Nguyen and Omar Espejel and Ona de Gibert and Paulo Villegas and Peter Henderson and Pierre Colombo and Priscilla Amuok and Quentin Lhoest and Rheza Harliman and Rishi Bommasani and Roberto Luis López and Rui Ribeiro and Salomey Osei and Sampo Pyysalo and Sebastian Nagel and Shamik Bose and Shamsuddeen Hassan Muhammad and Shanya Sharma and Shayne Longpre and Somaieh Nikpoor and Stanislav Silberberg and Suhas Pai and Sydney Zink and Tiago Timponi Torrent and Timo Schick and Tristan Thrush and Valentin Danchev and Vassilina Nikoulina and Veronika Laippala and Violette Lepercq and Vrinda Prabhu and Zaid Alyafeai and Zeerak Talat and Arun Raja and Benjamin Heinzerling and Chenglei Si and Davut Emre Taşar and Elizabeth Salesky and Sabrina J. Mielke and Wilson Y. Lee and Abheesht Sharma and Andrea Santilli and Antoine Chaffin and Arnaud Stiegler and Debajyoti Datta and Eliza Szczechla and Gunjan Chhablani and Han Wang and Harshit Pandey and Hendrik Strobelt and Jason Alan Fries and Jos Rozen and Leo Gao and Lintang Sutawika and M Saiful Bari and Maged S. Al-shaibani and Matteo Manica and Nihal Nayak and Ryan Teehan and Samuel Albanie and Sheng Shen and Srulik Ben-David and Stephen H. Bach and Taewoon Kim and Tali Bers and Thibault Fevry and Trishala Neeraj and Urmish Thakker and Vikas Raunak and Xiangru Tang and Zheng-Xin Yong and Zhiqing Sun and Shaked Brody and Yallow Uri and Hadar Tojarieh and Adam Roberts and Hyung Won Chung and Jaesung Tae and Jason Phang and Ofir Press and Conglong Li and Deepak Narayanan and Hatim Bourfoune and Jared Casper and Jeff Rasley and Max Ryabinin and Mayank Mishra and Minjia Zhang and Mohammad Shoeybi and Myriam Peyrounette and Nicolas Patry and Nouamane Tazi and Omar Sanseviero and Patrick von Platen and Pierre Cornette and Pierre François Lavallée and Rémi Lacroix and Samyam Rajbhandari and Sanchit Gandhi and Shaden Smith and Stéphane Requena and Suraj Patil and Tim Dettmers and Ahmed Baruwa and Amanpreet Singh and Anastasia Cheveleva and Anne-Laure Ligozat and Arjun Subramonian and Aurélie Névéol and Charles Lovering and Dan Garrette and Deepak Tunuguntla and Ehud Reiter and Ekaterina Taktasheva and Ekaterina Voloshina and Eli Bogdanov and Genta Indra Winata and Hailey Schoelkopf and Jan-Christoph Kalo and Jekaterina Novikova and Jessica Zosa Forde and Jordan Clive and Jungo Kasai and Ken Kawamura and Liam Hazan and Marine Carpuat and Miruna Clinciu and Najoung Kim and Newton Cheng and Oleg Serikov and Omer Antverg and Oskar van der Wal and Rui Zhang and Ruochen Zhang and Sebastian Gehrmann and Shachar Mirkin and Shani Pais and Tatiana Shavrina and Thomas Scialom and Tian Yun and Tomasz Limisiewicz and Verena Rieser and Vitaly Protasov and Vladislav Mikhailov and Yada Pruksachatkun and Yonatan Belinkov and Zachary Bamberger and Zdeněk Kasner and Alice Rueda and Amanda Pestana and Amir Feizpour and Ammar Khan and Amy Faranak and Ana Santos and Anthony Hevia and Antigona Unldreaj and Arash Aghagol and Arezoo Abdollahi and Aycha Tammour and Azadeh HajiHosseini and Bahareh Behroozi and Benjamin Ajibade and Bharat Saxena and Carlos Muñoz Ferrandis and Daniel McDuff and Danish Contractor and David Lansky and Davis David and Douwe Kiela and Duong A. Nguyen and Edward Tan and Emi Baylor and Ezinwanne Ozoani and Fatima Mirza and Frankline Ononiwu and Habib Rezanejad and Hessie Jones and Indrani Bhattacharya and Irene Solaiman and Irina Sedenko and Isar Nejadgholi and Jesse Passmore and Josh Seltzer and Julio Bonis Sanz and Livia Dutra and Mairon Samagaio and Maraim Elbadri and Margot Mieskes and Marissa Gerchick and Martha Akinlolu and Michael McKenna and Mike Qiu and Muhammed Ghauri and Mykola Burynok and Nafis Abrar and Nazneen Rajani and Nour Elkott and Nour Fahmy and Olanrewaju Samuel and Ran An and Rasmus Kromann and Ryan Hao and Samira Alizadeh and Sarmad Shubber and Silas Wang and Sourav Roy and Sylvain Viguier and Thanh Le and Tobi Oyebade and Trieu Le and Yoyo Yang and Zach Nguyen and Abhinav Ramesh Kashyap and Alfredo Palasciano and Alison Callahan and Anima Shukla and Antonio Miranda-Escalada and Ayush Singh and Benjamin Beilharz and Bo Wang and Caio Brito and Chenxi Zhou and Chirag Jain and Chuxin Xu and Clémentine Fourrier and Daniel León Periñán and Daniel Molano and Dian Yu and Enrique Manjavacas and Fabio Barth and Florian Fuhrimann and Gabriel Altay and Giyaseddin Bayrak and Gully Burns and Helena U. Vrabec and Imane Bello and Ishani Dash and Jihyun Kang and John Giorgi and Jonas Golde and Jose David Posada and Karthik Rangasai Sivaraman and Lokesh Bulchandani and Lu Liu and Luisa Shinzato and Madeleine Hahn de Bykhovetz and Maiko Takeuchi and Marc Pàmies and Maria A Castillo and Marianna Nezhurina and Mario Sänger and Matthias Samwald and Michael Cullan and Michael Weinberg and Michiel De Wolf and Mina Mihaljcic and Minna Liu and Moritz Freidank and Myungsun Kang and Natasha Seelam and Nathan Dahlberg and Nicholas Michio Broad and Nikolaus Muellner and Pascale Fung and Patrick Haller and Ramya Chandrasekhar and Renata Eisenberg and Robert Martin and Rodrigo Canalli and Rosaline Su and Ruisi Su and Samuel Cahyawijaya and Samuele Garda and Shlok S Deshmukh and Shubhanshu Mishra and Sid Kiblawi and Simon Ott and Sinee Sang-aroonsiri and Srishti Kumar and Stefan Schweter and Sushil Bharati and Tanmay Laud and Théo Gigant and Tomoya Kainuma and Wojciech Kusa and Yanis Labrak and Yash Shailesh Bajaj and Yash Venkatraman and Yifan Xu and Yingxin Xu and Yu Xu and Zhe Tan and Zhongli Xie and Zifan Ye and Mathilde Bras and Younes Belkada and Thomas Wolf},
  year = {2022},
  eprint = {2211.05100},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2211.05100}
}""",
        "training_data_sources": "",
    },
    "tinyllama-1.1b": {
        "description": "",
        "model_parameters": "1.1B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")""",
        "citation": """@misc{zhang2024,
  title = {TinyLlama: An Open-Source Small Language Model},
  author = {Peiyuan Zhang and Guangtao Zeng and Tianduo Wang and Wei Lu},
  year = {2024},
  eprint = {2401.02385},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2401.02385}
}""",
        "training_data_sources": "",
    },
    "gpt2": {
        "description": "",
        "model_parameters": "137M",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/openai-community/gpt2",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="openai-community/gpt2")""",
        "citation": "",
        "training_data_sources": "",
    },
    "phi-3.5-mini": {
        "description": "",
        "model_parameters": "3.8B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/microsoft/Phi-3.5-mini-instruct",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="microsoft/Phi-3.5-mini-instruct")""",
        "citation": """@misc{abdin2024,
  title = {Phi-3 Technical Report: A Highly Capable Language Model Locally on Your Phone},
  author = {Marah Abdin and Jyoti Aneja and Hany Awadalla and Ahmed Awadallah and Ammar Ahmad Awan and Nguyen Bach and Amit Bahree and Arash Bakhtiari and Jianmin Bao and Harkirat Behl and Alon Benhaim and Misha Bilenko and Johan Bjorck and Sébastien Bubeck and Martin Cai and Qin Cai and Vishrav Chaudhary and Dong Chen and Dongdong Chen and Weizhu Chen and Yen-Chun Chen and Yi-Ling Chen and Hao Cheng and Parul Chopra and Xiyang Dai and Matthew Dixon and Ronen Eldan and Victor Fragoso and Jianfeng Gao and Mei Gao and Min Gao and Amit Garg and Allie Del Giorno and Abhishek Goswami and Suriya Gunasekar and Emman Haider and Junheng Hao and Russell J. Hewett and Wenxiang Hu and Jamie Huynh and Dan Iter and Sam Ade Jacobs and Mojan Javaheripi and Xin Jin and Nikos Karampatziakis and Piero Kauffmann and Mahoud Khademi and Dongwoo Kim and Young Jin Kim and Lev Kurilenko and James R. Lee and Yin Tat Lee and Yuanzhi Li and Yunsheng Li and Chen Liang and Lars Liden and Xihui Lin and Zeqi Lin and Ce Liu and Liyuan Liu and Mengchen Liu and Weishung Liu and Xiaodong Liu and Chong Luo and Piyush Madan and Ali Mahmoudzadeh and David Majercak and Matt Mazzola and Caio César Teodoro Mendes and Arindam Mitra and Hardik Modi and Anh Nguyen and Brandon Norick and Barun Patra and Daniel Perez-Becker and Thomas Portet and Reid Pryzant and Heyang Qin and Marko Radmilac and Liliang Ren and Gustavo de Rosa and Corby Rosset and Sambudha Roy and Olatunji Ruwase and Olli Saarikivi and Amin Saied and Adil Salim and Michael Santacroce and Shital Shah and Ning Shang and Hiteshi Sharma and Yelong Shen and Swadheen Shukla and Xia Song and Masahiro Tanaka and Andrea Tupini and Praneetha Vaddamanu and Chunyu Wang and Guanhua Wang and Lijuan Wang and Shuohang Wang and Xin Wang and Yu Wang and Rachel Ward and Wen Wen and Philipp Witte and Haiping Wu and Xiaoxia Wu and Michael Wyatt and Bin Xiao and Can Xu and Jiahang Xu and Weijian Xu and Jilong Xue and Sonali Yadav and Fan Yang and Jianwei Yang and Yifan Yang and Ziyi Yang and Donghan Yu and Lu Yuan and Chenruidong Zhang and Cyril Zhang and Jianwen Zhang and Li Lyna Zhang and Yi Zhang and Yue Zhang and Yunan Zhang and Xiren Zhou},
  year = {2024},
  eprint = {2404.14219},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2404.14219}
}""",
        "training_data_sources": "",
    },
    "qwen2.5-1.5b": {
        "description": "",
        "model_parameters": "1.5B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "domain": "language",
        "category": "text_generation",
        "task_type": "text-generation",
        "huggingface_url": "https://huggingface.co/Qwen/Qwen2.5-1.5B",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("text-generation", model="Qwen/Qwen2.5-1.5B")""",
        "citation": """@misc{qwen2024,
  title = {Qwen2.5 Technical Report},
  author = { Qwen and  : and An Yang and Baosong Yang and Beichen Zhang and Binyuan Hui and Bo Zheng and Bowen Yu and Chengyuan Li and Dayiheng Liu and Fei Huang and Haoran Wei and Huan Lin and Jian Yang and Jianhong Tu and Jianwei Zhang and Jianxin Yang and Jiaxi Yang and Jingren Zhou and Junyang Lin and Kai Dang and Keming Lu and Keqin Bao and Kexin Yang and Le Yu and Mei Li and Mingfeng Xue and Pei Zhang and Qin Zhu and Rui Men and Runji Lin and Tianhao Li and Tianyi Tang and Tingyu Xia and Xingzhang Ren and Xuancheng Ren and Yang Fan and Yang Su and Yichang Zhang and Yu Wan and Yuqiong Liu and Zeyu Cui and Zhenru Zhang and Zihan Qiu},
  year = {2024},
  eprint = {2412.15115},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2412.15115}
}""",
        "training_data_sources": "",
    },
}
