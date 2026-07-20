MULTI_MODAL_MODELS = {
    "clip-vit-base": {
        "model_parameters": "151M",
        "model_architecture": "ViT-B/32 Transformer for image encoding + Masked self-attention Transformer for text encoding. Uses contrastive learning to maximize similarity of (image, text) pairs",
        "training_data_sources": "WebImageText (WIT-400M) - approximately 400M image-text pairs collected from the web",
        "huggingface_url": "https://huggingface.co/openai/clip-vit-base-patch32",
        "input_modalities": ["image", "text"],
        "output_modalities": ["embeddings"],
        "image_size": "224x224",
        "dependent_packages": ["transformers", "PIL", "requests", "torch"],
        "code": """from PIL import Image
import requests
from transformers import CLIPProcessor, CLIPModel

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

url = "http://images.cocodataset.org/val2017/000000039769.jpg"
image = Image.open(requests.get(url, stream=True).raw)

inputs = processor(text=["a photo of a cat", "a photo of a dog"], images=image, return_tensors="pt", padding=True)
outputs = model(**inputs)
logits_per_image = outputs.logits_per_image
probs = logits_per_image.softmax(dim=1)""",
        "citation": """
@misc{radford2021learning,
  title = {Learning Transferable Visual Models From Natural Language Supervision},
  author = {Radford, Alec and Kim, Jong Wook and Hallacy, Chris and Ramesh, Aditya and Goh, Gabriel and Agarwal, Sandhini and Sastry, Girish and Askell, Amanda and Mishkin, Pamela and Clark, Jack and Krueger, Gretchen and Sutskever, Ilya},
  year = {2021},
  archivePrefix = {arXiv},
  eprint = {2103.00020},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2103.00020}
}
""",
        "task_type": "image-classification",
    },
    "blip-image-captioning": {
        "model_parameters": "129M",
        "model_architecture": "Vision-Language Pre-training framework with ViT-B backbone for image encoding + BERT-like text encoder/decoder. Uses bootstrapping with captioner and filter (CapFilt) method",
        "training_data_sources": "129M image-text pairs from COCO, Visual Genome, Conceptual Captions (CC3M, CC12M), SBU captions, and LAION400M",
        "huggingface_url": "https://huggingface.co/Salesforce/blip-image-captioning-base",
        "input_modalities": ["image", "text"],
        "output_modalities": ["text"],
        "image_size": "384x384",
        "dependent_packages": ["transformers", "PIL", "requests", "torch"],
        "code": """import requests
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

img_url = 'https://storage.googleapis.com/sfr-vision-language-research/BLIP/demo.jpg'
raw_image = Image.open(requests.get(img_url, stream=True).raw).convert('RGB')

# conditional image captioning
text = "a photography of"
inputs = processor(raw_image, text, return_tensors="pt")
out = model.generate(**inputs)
print(processor.decode(out[0], skip_special_tokens=True))

# unconditional image captioning
inputs = processor(raw_image, return_tensors="pt")
out = model.generate(**inputs)
print(processor.decode(out[0], skip_special_tokens=True))""",
        "citation": """
@misc{li2022blip,
  title = {BLIP: Bootstrapping Language-Image Pre-training for Unified Vision-Language Understanding and Generation},
  author = {Li, Junnan and Li, Dongxu and Xiong, Caiming and Hoi, Steven},
  year = {2022},
  archivePrefix = {arXiv},
  eprint = {2201.12086},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2201.12086}
}""",
        "task_type": "image-captioning",
    },
    "llava-1.5-7b": {
        "model_parameters": "7.1B",
        "model_architecture": "Vision-language multimodal model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/llava-hf/llava-1.5-7b-hf",
        "task_type": "image-text-to-text",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("image-text-to-text", model="llava-hf/llava-1.5-7b-hf")""",
        "citation": """@misc{liu2023,
  title = {Improved Baselines with Visual Instruction Tuning},
  author = {Haotian Liu and Chunyuan Li and Yuheng Li and Yong Jae Lee},
  year = {2023},
  eprint = {2310.03744},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2310.03744}
}""",
    },
    "qwen2-vl-7b": {
        "model_parameters": "8.3B",
        "model_architecture": "Vision-language multimodal model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct",
        "task_type": "image-text-to-text",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("image-text-to-text", model="Qwen/Qwen2-VL-7B-Instruct")""",
        "citation": """@misc{wang2024,
  title = {Qwen2-VL: Enhancing Vision-Language Model's Perception of the World at Any Resolution},
  author = {Peng Wang and Shuai Bai and Sinan Tan and Shijie Wang and Zhihao Fan and Jinze Bai and Keqin Chen and Xuejing Liu and Jialin Wang and Wenbin Ge and Yang Fan and Kai Dang and Mengfei Du and Xuancheng Ren and Rui Men and Dayiheng Liu and Chang Zhou and Jingren Zhou and Junyang Lin},
  year = {2024},
  eprint = {2409.12191},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2409.12191}
}""",
    },
    "blip2-opt-2.7b": {
        "model_parameters": "3.7B",
        "model_architecture": "Vision-language multimodal model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/Salesforce/blip2-opt-2.7b",
        "task_type": "image-text-to-text",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("image-text-to-text", model="Salesforce/blip2-opt-2.7b")""",
        "citation": """@misc{li2023,
  title = {BLIP-2: Bootstrapping Language-Image Pre-training with Frozen Image Encoders and Large Language Models},
  author = {Junnan Li and Dongxu Li and Silvio Savarese and Steven Hoi},
  year = {2023},
  eprint = {2301.12597},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2301.12597}
}""",
    },
    "siglip-base": {
        "model_parameters": "203M",
        "model_architecture": "Vision-language multimodal model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/google/siglip-base-patch16-224",
        "task_type": "zero-shot-image-classification",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("zero-shot-image-classification", model="google/siglip-base-patch16-224")""",
        "citation": """@misc{zhai2023,
  title = {Sigmoid Loss for Language Image Pre-Training},
  author = {Xiaohua Zhai and Basil Mustafa and Alexander Kolesnikov and Lucas Beyer},
  year = {2023},
  eprint = {2303.15343},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2303.15343}
}""",
    },
    "idefics2-8b": {
        "model_parameters": "8.4B",
        "model_architecture": "Vision-language multimodal model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/HuggingFaceM4/idefics2-8b",
        "task_type": "image-text-to-text",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("image-text-to-text", model="HuggingFaceM4/idefics2-8b")""",
        "citation": """@misc{laurençon2024,
  title = {What matters when building vision-language models?},
  author = {Hugo Laurençon and Léo Tronchon and Matthieu Cord and Victor Sanh},
  year = {2024},
  eprint = {2405.02246},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2405.02246}
}""",
    },
    "instructblip-vicuna-7b": {
        "model_parameters": "7.9B",
        "model_architecture": "Vision-language multimodal model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/Salesforce/instructblip-vicuna-7b",
        "task_type": "image-text-to-text",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("image-text-to-text", model="Salesforce/instructblip-vicuna-7b")""",
        "citation": """@misc{dai2023,
  title = {InstructBLIP: Towards General-purpose Vision-Language Models with Instruction Tuning},
  author = {Wenliang Dai and Junnan Li and Dongxu Li and Anthony Meng Huat Tiong and Junqi Zhao and Weisheng Wang and Boyang Li and Pascale Fung and Steven Hoi},
  year = {2023},
  eprint = {2305.06500},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2305.06500}
}""",
    },
    "qwen2.5-vl-7b": {
        "model_parameters": "8.3B",
        "model_architecture": "Vision-language multimodal model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct",
        "task_type": "image-text-to-text",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("image-text-to-text", model="Qwen/Qwen2.5-VL-7B-Instruct")""",
        "citation": """@misc{bai2025,
  title = {Qwen2.5-VL Technical Report},
  author = {Shuai Bai and Keqin Chen and Xuejing Liu and Jialin Wang and Wenbin Ge and Sibo Song and Kai Dang and Peng Wang and Shijie Wang and Jun Tang and Humen Zhong and Yuanzhi Zhu and Mingkun Yang and Zhaohai Li and Jianqiang Wan and Pengfei Wang and Wei Ding and Zheren Fu and Yiheng Xu and Jiabo Ye and Xi Zhang and Tianbao Xie and Zesen Cheng and Hang Zhang and Zhibo Yang and Haiyang Xu and Junyang Lin},
  year = {2025},
  eprint = {2502.13923},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2502.13923}
}""",
    },
    "internvl2-8b": {
        "model_parameters": "8.1B",
        "model_architecture": "Vision-language multimodal model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/OpenGVLab/InternVL2-8B",
        "task_type": "image-text-to-text",
        "dependent_packages": ["transformers", "torch"],
        "code": """from transformers import pipeline
pipe = pipeline("image-text-to-text", model="OpenGVLab/InternVL2-8B")""",
        "citation": """@misc{chen2024,
  title = {How Far Are We to GPT-4V? Closing the Gap to Commercial Multimodal Models with Open-Source Suites},
  author = {Zhe Chen and Weiyun Wang and Hao Tian and Shenglong Ye and Zhangwei Gao and Erfei Cui and Wenwen Tong and Kongzhi Hu and Jiapeng Luo and Zheng Ma and Ji Ma and Jiaqi Wang and Xiaoyi Dong and Hang Yan and Hewei Guo and Conghui He and Botian Shi and Zhenjiang Jin and Chao Xu and Bin Wang and Xingjian Wei and Wei Li and Wenjian Zhang and Bo Zhang and Pinlong Cai and Licheng Wen and Xiangchao Yan and Min Dou and Lewei Lu and Xizhou Zhu and Tong Lu and Dahua Lin and Yu Qiao and Jifeng Dai and Wenhai Wang},
  year = {2024},
  eprint = {2404.16821},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2404.16821}
}""",
    },
}
