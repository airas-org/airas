TRANSFORMER_DECODER_BASED_MODELS = {
    # Llama 4
    "Llama-4-Scout-17B-16E": {
        "model_parameters": {
            "total_parameters": "109b",
            "active_parameters": "17b",
        },
        "model_architecture": "Transformer-based Mixture-of-Experts (MoE) architecture",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E",
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "dependent_packages": [],
        "code": """\
from transformers import pipeline
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
        "citation": """\
@misc{meta2024llama4,
  title = {Introducing LLaMA 4: Advancing Multimodal Intelligence},
  author = {Meta AI},
  year = {2024},
  url = {https://ai.meta.com/blog/llama-4-multimodal-intelligence/}
}""",
    },
    "Llama-4-Maverick-17B-128E": {
        "model_parameters": {
            "total_parameters": "400b",
            "active_parameters": "17b",
        },
        "model_architecture": "Transformer-based Mixture-of-Experts (MoE) architecture",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E",
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "dependent_packages": [],
        "code": """\
from transformers import pipeline
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
        "citation": """\
@misc{meta2024llama4,
  title = {Introducing LLaMA 4: Advancing Multimodal Intelligence},
  author = {Meta AI},
  year = {2024},
  url = {https://ai.meta.com/blog/llama-4-multimodal-intelligence/}
}""",
    },
    # Qwen 3
    "Qwen3-0.6B": {
        "model_parameters": "0.6b",
        "model_architecture": "Transformer",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/Qwen/Qwen3-0.6B",
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "dependent_packages": ["transformers>=4.51.0"],
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
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "dependent_packages": ["transformers>=4.51.0"],
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
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "dependent_packages": ["transformers>=4.51.0"],
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
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "dependent_packages": ["transformers>=4.51.0"],
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
        "task_type": "text-generation",
        "language_distribution": "",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "dependent_packages": ["transformers>=4.51.0"],
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
        "task_type": "text-generation",
        "language_distribution": "",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "dependent_packages": ["transformers>=4.51.0"],
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
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "dependent_packages": [],
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
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "dependent_packages": [],
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
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "dependent_packages": [],
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
        "task_type": "text-generation",
        "context_length": "",
        "language_distribution": "multilingual",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "dependent_packages": ["accelerate", "transformers", "kernels"],
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
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "dependent_packages": ["transformers"],
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
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "dependent_packages": ["transformers"],
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
        "task_type": "text-generation",
        "language_distribution": "Multilingual",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "dependent_packages": ["transformers"],
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
    "Mistral-7B-v0.3": {
        "model_parameters": "7.3B",
        "model_architecture": "Transformer decoder with Grouped-Query Attention (GQA), Sliding-Window Attention, Byte-fallback BPE tokenizer, extended vocabulary to 32,768 tokens",
        "training_data_sources": "Large-scale web data (proprietary, not publicly disclosed in detail)",
        "huggingface_url": "https://huggingface.co/mistralai/Mistral-7B-v0.3",
        "task_type": "text-generation",
        "language_distribution": "Primarily English (multilingual capabilities present)",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "dependent_packages": [
            "transformers",
            "torch",
            "mistral-inference (recommended)",
            "huggingface-hub",
        ],
        "code": """\
from transformers import AutoModelForCausalLM, AutoTokenizer
model_id = "mistralai/Mistral-7B-v0.3"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)

inputs = tokenizer("Hello my name is", return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=20)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))""",
        "citation": "@article{jiang2023mistral, title={Mistral 7B}, author={Albert Q. Jiang and Alexandre Sablayrolles and Arthur Mensch and others}, journal={arXiv preprint arXiv:2310.06825}, year={2023}}",
    },
    "mistral-7b-v0.3": {
        "model_parameters": "7.2B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/mistralai/Mistral-7B-v0.3",
        "task_type": "text-generation",
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
    },
    "phi-3-mini-4k-instruct": {
        "model_parameters": "3.8B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct",
        "task_type": "text-generation",
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
    },
    "falcon-7b": {
        "model_parameters": "7.2B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/tiiuae/falcon-7b",
        "task_type": "text-generation",
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
    },
    "pythia-1.4b": {
        "model_parameters": "1.5B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/EleutherAI/pythia-1.4b",
        "task_type": "text-generation",
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
    },
    "olmo-2-1124-7b": {
        "model_parameters": "7.3B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/allenai/OLMo-2-1124-7B",
        "task_type": "text-generation",
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
    },
    "smollm2-1.7b": {
        "model_parameters": "1.7B",
        "model_architecture": "Decoder-only autoregressive transformer language model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B",
        "task_type": "text-generation",
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
    },
}
