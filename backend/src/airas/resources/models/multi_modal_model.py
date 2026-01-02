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
}
