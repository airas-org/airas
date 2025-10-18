MODEL_LIST = {
    "Large Language Models": {
        # Llama 4
        "Llama-4-Scout-17B-16E": {
            "model_parameters": {
                "total_parameters": "109b",
                "active_parameters": "17b",
            },
            "model_architecture": "Transformer-based Mixture-of-Experts (MoE) architecture",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E",
            "language_distribution": "Multilingual",
            "input_modalities": ["text", "image"],
            "output_modalities": ["text"],
            "dependent packages": [],
            "code": """\
""",
            "citation": """\
""",
        },
        "Llama-4-Maverick-17B-128E": {
            "model_parameters": {
                "total_parameters": "400b",
                "active_parameters": "17b",
            },
            "model_architecture": "Transformer-based Mixture-of-Experts (MoE) architecture",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E",
            "language_distribution": "Multilingual",
            "input_modalities": ["text", "image"],
            "output_modalities": ["text"],
            "dependent packages": [],
            "code": """\
""",
            "citation": """\
""",
        },
        # Qwen 3
        "Qwen3-0.6B": {
            "model_parameters": "0.6b",
            "model_architecture": "Transformer",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/Qwen/Qwen3-0.6B",
            "language_distribution": "Multilingual",
            "input_modalities": ["text"],
            "output_modalities": ["text"],
            "dependent packages": ["transformers>=4.51.0"],
            "code": """\
from transformers import AutoModelForCausalLM, AutoTokenizer
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
            "citation": """\
@misc{qwen3technicalreport,
      title={Qwen3 Technical Report},
      author={Qwen Team},
      year={2025},
      eprint={2505.09388},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2505.09388},
}""",
        },
        "Qwen3-1.7B": {
            "model_parameters": "1.7b",
            "model_architecture": "Transformer",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/Qwen/Qwen3-1.7B",
            "language_distribution": "Multilingual",
            "input_modalities": ["text"],
            "output_modalities": ["text"],
            "dependent packages": ["transformers>=4.51.0"],
            "code": """\
from transformers import AutoModelForCausalLM, AutoTokenizer
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
            "citation": """\
@misc{qwen3technicalreport,
      title={Qwen3 Technical Report},
      author={Qwen Team},
      year={2025},
      eprint={2505.09388},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2505.09388},
}""",
        },
        "Qwen3-4B": {
            "model_parameters": "4b",
            "model_architecture": "Transformer",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/Qwen/Qwen3-4B",
            "language_distribution": "Multilingual",
            "input_modalities": ["text"],
            "output_modalities": ["text"],
            "dependent packages": ["transformers>=4.51.0"],
            "code": """\
from transformers import AutoModelForCausalLM, AutoTokenizer

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
            "citation": """\
@misc{qwen3technicalreport,
      title={Qwen3 Technical Report},
      author={Qwen Team},
      year={2025},
      eprint={2505.09388},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2505.09388},
}""",
        },
        "Qwen3-8B": {
            "model_parameters": "8b",
            "model_architecture": "Transformer",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/Qwen/Qwen3-8B",
            "language_distribution": "Multilingual",
            "input_modalities": ["text"],
            "output_modalities": ["text"],
            "dependent packages": ["transformers>=4.51.0"],
            "code": """\
from transformers import AutoModelForCausalLM, AutoTokenizer
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
            "citation": """\
@misc{qwen3technicalreport,
      title={Qwen3 Technical Report},
      author={Qwen Team},
      year={2025},
      eprint={2505.09388},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2505.09388},
}""",
        },
        "Qwen3-14B": {
            "model_parameters": "14b",
            "model_architecture": "Transformer",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/Qwen/Qwen3-14B",
            "language_distribution": "",
            "input_modalities": ["text"],
            "output_modalities": ["text"],
            "dependent packages": ["transformers>=4.51.0"],
            "code": """\
from transformers import AutoModelForCausalLM, AutoTokenizer

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
            "citation": """\
@misc{qwen3technicalreport,
      title={Qwen3 Technical Report},
      author={Qwen Team},
      year={2025},
      eprint={2505.09388},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2505.09388},
}""",
        },
        "Qwen3-32B": {
            "model_parameters": "32.8b",
            "model_architecture": "Transformer",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/Qwen/Qwen3-32B",
            "language_distribution": "",
            "input_modalities": ["text"],
            "output_modalities": ["text"],
            "dependent packages": ["transformers>=4.51.0"],
            "code": """\
from transformers import AutoModelForCausalLM, AutoTokenizer

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
            "citation": """\
@misc{qwen3technicalreport,
      title={Qwen3 Technical Report},
      author={Qwen Team},
      year={2025},
      eprint={2505.09388},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2505.09388},
}""",
        },
        # Deepseek
        "DeepSeek-v3": {
            "model_parameters": {
                "total_parameters": "671b",
                "active_parameters": "37b",
            },
            "model_architecture": "Transformer-based Mixture-of-Experts (MoE) architecture",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/deepseek-ai/DeepSeek-V3",
            "language_distribution": "Multilingual",
            "input_modalities": ["text"],
            "output_modalities": ["text"],
            "dependent packages": [],
            "code": """\
""",
            "citation": """\
@misc{deepseekai2024deepseekv3technicalreport,
      title={DeepSeek-V3 Technical Report},
      author={DeepSeek-AI},
      year={2024},
      eprint={2412.19437},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2412.19437},
}""",
        },
        "DeepSeek-V3.1": {
            "model_parameters": {
                "total_parameters": "671B",
                "active_parameters": "37B",
            },
            "model_architecture": "Transformer-based Mixture-of-Experts (MoE) architecture",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/deepseek-ai/DeepSeek-V3.1",
            "language_distribution": "Multilingual",
            "input_modalities": ["Text"],
            "output_modalities": ["Text"],
            "dependent packages": [],
            "code": """\
""",
            "citation": """\
@misc{deepseekai2024deepseekv3technicalreport,
      title={DeepSeek-V3 Technical Report},
      author={DeepSeek-AI},
      year={2024},
      eprint={2412.19437},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2412.19437},
}""",
        },
        "DeepSeek-V3.2-Exp": {
            "model_parameters": {
                "total_parameters": "671B",
                "active_parameters": "37B",
            },
            "model_architecture": "Transformer-based Mixture-of-Experts (MoE) architecture",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/deepseek-ai/DeepSeek-V3.2-Exp",
            "language_distribution": "Multilingual",
            "input_modalities": ["Text"],
            "output_modalities": ["Text"],
            "dependent packages": [],
            "code": """\
""",
            "citation": """\
@misc{deepseekai2024deepseekv32,
      title={DeepSeek-V3.2-Exp: Boosting Long-Context Efficiency with DeepSeek Sparse Attention},
      author={DeepSeek-AI},
      year={2025},
}""",
        },
        # gpt-oss
        "gpt-oss-20b": {
            "model_parameters": {
                "total_parameters": "21b",
                "active_parameters": "3.6b",
            },
            "model_architecture": "Transformer-based Mixture-of-Experts (MoE) architecture",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/openai/gpt-oss-20b",
            "context_length": "",
            "language_distribution": "multilingual",
            "input_modalities": "text",
            "output_modalities": "text",
            "dependent packages": ["accelerate", "transformers", "kernels"],
            "code": """\
from transformers import AutoModelForCausalLM, AutoTokenizer
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
            "citation": """\
@misc{openai2025gptoss120bgptoss20bmodel,
      title={gpt-oss-120b & gpt-oss-20b Model Card},
      author={OpenAI},
      year={2025},
      eprint={2508.10925},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2508.10925},
}""",
        },
        # Genma
        "gemma-3-1b-it": {
            "model_parameters": "1b",
            "model_architecture": "Transformer",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/google/gemma-3-1b-it",
            "language_distribution": "Multilingual",
            "input_modalities": ["text", "image"],
            "output_modalities": ["text"],
            "dependent packages": ["transformers"],
            "code": """\
from transformers import AutoTokenizer, AutoModelForCausalLM

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
            "citation": """\
@article{gemma_2025,
    title={Gemma 3},
    url={https://goo.gle/Gemma3Report},
    publisher={Kaggle},
    author={Gemma Team},
    year={2025}
}""",
        },
        "gemma-3-4b-it": {
            "model_parameters": "4b",
            "model_architecture": "Transformer",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/google/gemma-3-4b-it",
            "language_distribution": "Multilingual",
            "input_modalities": ["text", "image"],
            "output_modalities": ["text"],
            "dependent packages": ["transformers"],
            "code": """\
from transformers import AutoTokenizer, AutoModelForCausalLM

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
            "citation": """\
@article{gemma_2025,
    title={Gemma 3},
    url={https://goo.gle/Gemma3Report},
    publisher={Kaggle},
    author={Gemma Team},
    year={2025}
}""",
        },
        "gemma-3-27b-it": {
            "model_parameters": "27b",
            "model_architecture": "Transformer",
            "training_data_sources": "",
            "huggingface_url": "https://huggingface.co/google/gemma-3-27b-it",
            "language_distribution": "Multilingual",
            "input_modalities": ["text", "image"],
            "output_modalities": ["text"],
            "dependent packages": ["transformers"],
            "code": """\
from transformers import AutoTokenizer, AutoModelForCausalLM

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
            "citation": """\
@article{gemma_2025,
    title={Gemma 3},
    url={https://goo.gle/Gemma3Report},
    publisher={Kaggle},
    author={Gemma Team},
    year={2025}
}""",
        },
        # Mistral
        # Sample
        #         "sample": {
        #             "model_parameters": "",
        #             "model_architecture": "",
        #             "training_data_sources": "",
        #             "huggingface_url": "",
        #             "language_distribution": "",
        #             "input_modalities": [],
        #             "output_modalities": [],
        #             "dependent packages": [],
        #             "code": """\
        # """,
        #             "citation": """\
        # """
        #         },
    },
    "Vision Language Models": {},
    "Vision Language Action Models": {},
    "Diffusion Models": {},
}
