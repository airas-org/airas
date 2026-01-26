IMAGE_MODELS = {
    # ========================================
    # Image classification and feature extraction
    # ========================================
    ## Vision Transformers
    "vit-base": {
        "model_parameters": "86M",
        "model_architecture": "Transformer encoder model (BERT-like) that processes images as sequences of fixed-size patches (16x16). Images are linearly embedded with absolute position embeddings and a [CLS] token for classification. Contains 12 transformer encoder layers with 12 attention heads and 768 hidden dimensions.",
        "training_data_sources": "Pre-trained on ImageNet-21k (14 million images, 21,843 classes), fine-tuned on ImageNet-1k (1 million images, 1,000 classes)",
        "huggingface_url": "https://huggingface.co/google/vit-base-patch16-224",
        "input_modalities": ["image"],
        "image_size": "224x224",
        "dependent_packages": ["transformers", "torch", "PIL", "requests"],
        "code": """from transformers import ViTImageProcessor, ViTForImageClassification
from PIL import Image
import requests

url = 'http://images.cocodataset.org/val2017/000000039769.jpg'
image = Image.open(requests.get(url, stream=True).raw)

processor = ViTImageProcessor.from_pretrained('google/vit-base-patch16-224')
model = ViTForImageClassification.from_pretrained('google/vit-base-patch16-224')

inputs = processor(images=image, return_tensors="pt")
outputs = model(**inputs)
logits = outputs.logits

# model predicts one of the 1000 ImageNet classes
predicted_class_idx = logits.argmax(-1).item()
print("Predicted class:", model.config.id2label[predicted_class_idx])""",
        "citation": """
@misc{dosovitskiy2020image,
  title = {An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale},
  author = {Dosovitskiy, Alexey and Beyer, Lucas and Kolesnikov, Alexander and Weissenborn, Dirk and Zhai, Xiaohua and Unterthiner, Thomas and Dehghani, Mostafa and Minderer, Matthias and Heigold, Georg and Gelly, Sylvain and Uszkoreit, Jakob and Houlsby, Neil},
  year = {2020},
  archivePrefix = {arXiv},
  eprint = {2010.11929},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2010.11929}
}""",
        "task_type": "image-classification",
    },
    "deit-base": {
        "model_parameters": "86M",
        "model_architecture": "More efficiently trained Vision Transformer (ViT) model with the same architecture as ViT-Base. Uses transformer encoder with 12 layers, 12 attention heads, 768 hidden dimensions. Processes images as sequences of 16x16 patches with linear embeddings and absolute position embeddings.",
        "training_data_sources": "ImageNet-1k (1 million images, 1,000 classes) - trained without external data",
        "huggingface_url": "https://huggingface.co/facebook/deit-base-patch16-224",
        "input_modalities": ["image"],
        "image_size": "224x224",
        "dependent_packages": ["transformers", "torch", "PIL", "requests"],
        "code": """from transformers import AutoFeatureExtractor, ViTForImageClassification
from PIL import Image
import requests

url = 'http://images.cocodataset.org/val2017/000000039769.jpg'
image = Image.open(requests.get(url, stream=True).raw)

feature_extractor = AutoFeatureExtractor.from_pretrained('facebook/deit-base-patch16-224')
model = ViTForImageClassification.from_pretrained('facebook/deit-base-patch16-224')

inputs = feature_extractor(images=image, return_tensors="pt")
outputs = model(**inputs)
logits = outputs.logits

predicted_class_idx = logits.argmax(-1).item()
print("Predicted class:", model.config.id2label[predicted_class_idx])""",
        "citation": """
@misc{touvron2020deit,
  title = {Training data-efficient image transformers distillation through attention},
  author = {Touvron, Hugo and Cord, Matthieu and Douze, Matthijs and Massa, Francisco and Sablayrolles, Alexandre and Jegou, Herve},
  year = {2020},
  archivePrefix = {arXiv},
  eprint = {2012.12877},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2012.12877}
}""",
        "task_type": "image-classification",
    },
    "beit-base": {
        "model_parameters": "86M",
        "model_architecture": "Vision Transformer (ViT) with BERT-like architecture pre-trained using masked image modeling. Images are processed as sequences of 16x16 patches. Uses relative position embeddings (similar to T5) instead of absolute position embeddings. Classification performed by mean-pooling final hidden states of patches.",
        "training_data_sources": "Pre-trained on ImageNet-21k (14 million images, 21,841 classes) using self-supervised learning (predicting visual tokens from DALL-E's VQ-VAE), fine-tuned on ImageNet-1k (1 million images, 1,000 classes)",
        "huggingface_url": "https://huggingface.co/microsoft/beit-base-patch16-224",
        "input_modalities": ["image"],
        "image_size": "224x224",
        "dependent_packages": ["transformers", "torch", "PIL", "requests"],
        "code": """from transformers import BeitImageProcessor, BeitForImageClassification
from PIL import Image
import requests

url = 'http://images.cocodataset.org/val2017/000000039769.jpg'
image = Image.open(requests.get(url, stream=True).raw)

processor = BeitImageProcessor.from_pretrained('microsoft/beit-base-patch16-224')
model = BeitForImageClassification.from_pretrained('microsoft/beit-base-patch16-224')

inputs = processor(images=image, return_tensors="pt")
outputs = model(**inputs)
logits = outputs.logits

predicted_class_idx = logits.argmax(-1).item()
print("Predicted class:", model.config.id2label[predicted_class_idx])""",
        "citation": """
@misc{bao2021beit,
  title = {BEiT: BERT Pre-Training of Image Transformers},
  author = {Bao, Hangbo and Dong, Li and Piao, Songhao and Wei, Furu},
  year = {2021},
  archivePrefix = {arXiv},
  eprint = {2106.08254},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2106.08254}
}""",
        "task_type": "image-classification",
    },
    "dino-vitb16": {
        "model_parameters": "86M",
        "model_architecture": "Vision Transformer (ViT) base model trained using self-supervised DINO method. Uses transformer encoder with 12 layers, 12 attention heads, 768 hidden dimensions. Processes images as sequences of 16x16 patches with linear embeddings and absolute position embeddings. Note: This model does not include fine-tuned classification heads - it's a feature extractor.",
        "training_data_sources": "ImageNet-1k (1 million images) - self-supervised training without labels",
        "huggingface_url": "https://huggingface.co/facebook/dino-vitb16",
        "input_modalities": ["image"],
        "image_size": "224x224",
        "dependent_packages": ["transformers", "torch", "PIL", "requests"],
        "code": """from transformers import ViTImageProcessor, ViTModel
from PIL import Image
import requests

url = 'http://images.cocodataset.org/val2017/000000039769.jpg'
image = Image.open(requests.get(url, stream=True).raw)

processor = ViTImageProcessor.from_pretrained('facebook/dino-vitb16')
model = ViTModel.from_pretrained('facebook/dino-vitb16')

inputs = processor(images=image, return_tensors="pt")
outputs = model(**inputs)
last_hidden_states = outputs.last_hidden_state""",
        "citation": """
@misc{caron2021dino,
  title = {Emerging Properties in Self-Supervised Vision Transformers},
  author = {Caron, Mathilde and Touvron, Hugo and Misra, Ishan and Jegou, Herve and Mairal, Julien and Bojanowski, Piotr and Joulin, Armand},
  year = {2021},
  archivePrefix = {arXiv},
  eprint = {2104.14294},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2104.14294}
}""",
        "task_type": "image-classification",
    },
    ## CNN Architectures
    "resnet-50": {
        "model_parameters": "25.6M",
        "model_architecture": "ResNet (Residual Network) is a convolutional neural network using residual learning and skip connections. This is ResNet v1.5 with 50 layers (48 convolutional layers, 1 MaxPool layer, and 1 average pool layer). Uses bottleneck blocks with stride = 2 in the 3x3 convolution.",
        "training_data_sources": "ImageNet-1k",
        "huggingface_url": "https://huggingface.co/microsoft/resnet-50",
        "input_modalities": ["image"],
        "image_size": "224x224",
        "dependent_packages": ["transformers", "torch", "datasets", "PIL"],
        "code": """from transformers import AutoImageProcessor, ResNetForImageClassification
import torch
from datasets import load_dataset

dataset = load_dataset("huggingface/cats-image")
image = dataset["test"]["image"][0]

processor = AutoImageProcessor.from_pretrained("microsoft/resnet-50")
model = ResNetForImageClassification.from_pretrained("microsoft/resnet-50")

inputs = processor(image, return_tensors="pt")

with torch.no_grad():
    logits = model(**inputs).logits

predicted_label = logits.argmax(-1).item()
print(model.config.id2label[predicted_label])""",
        "citation": """
@misc{he2015resnet,
  title = {Deep Residual Learning for Image Recognition},
  author = {He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
  year = {2015},
  archivePrefix = {arXiv},
  eprint = {1512.03385},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/1512.03385}
}""",
        "task_type": "image-classification",
    },
    "efficientnet-b0": {
        "model_parameters": "5.3M",
        "model_architecture": "EfficientNet is a mobile-friendly pure convolutional model (ConvNet) that uses compound scaling method to uniformly scale all dimensions of depth/width/resolution using a compound coefficient. Based on inverted bottleneck residual blocks of MobileNetV2 with squeeze-and-excitation blocks. EfficientNet-B0 is the baseline model discovered through Neural Architecture Search (NAS).",
        "training_data_sources": "ImageNet-1k",
        "huggingface_url": "https://huggingface.co/google/efficientnet-b0",
        "input_modalities": ["image"],
        "image_size": "224x224",
        "dependent_packages": ["transformers", "torch", "datasets"],
        "code": """import torch
from datasets import load_dataset
from transformers import EfficientNetImageProcessor, EfficientNetForImageClassification

dataset = load_dataset("huggingface/cats-image")
image = dataset["test"]["image"][0]

preprocessor = EfficientNetImageProcessor.from_pretrained("google/efficientnet-b0")
model = EfficientNetForImageClassification.from_pretrained("google/efficientnet-b0")

inputs = preprocessor(image, return_tensors="pt")

with torch.no_grad():
    logits = model(**inputs).logits

predicted_label = logits.argmax(-1).item()
print(model.config.id2label[predicted_label])""",
        "citation": """
@misc{tan2019efficientnet,
  title = {EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks},
  author = {Tan, Mingxing and Le, Quoc V.},
  year = {2019},
  archivePrefix = {arXiv},
  eprint = {1905.11946},
  primaryClass = {cs.LG},
  url = {https://arxiv.org/abs/1905.11946}
}""",
        "task_type": "image-classification",
    },
    "convnext-base": {
        "model_parameters": "89M",
        "model_architecture": "ConvNeXT is a pure convolutional model (ConvNet) inspired by the design of Vision Transformers. Started from ResNet architecture and 'modernized' its design by taking the Swin Transformer as inspiration. Uses depthwise convolutions, inverted bottleneck design, larger kernels (7x7), and GELU activation.",
        "training_data_sources": "ImageNet-1k",
        "huggingface_url": "https://huggingface.co/facebook/convnext-base-224",
        "input_modalities": ["image"],
        "image_size": "224x224",
        "dependent_packages": ["transformers", "torch", "datasets"],
        "code": """from transformers import ConvNextImageProcessor, ConvNextForImageClassification
import torch
from datasets import load_dataset

dataset = load_dataset("huggingface/cats-image")
image = dataset["test"]["image"][0]

processor = ConvNextImageProcessor.from_pretrained("facebook/convnext-base-224")
model = ConvNextForImageClassification.from_pretrained("facebook/convnext-base-224")

inputs = processor(image, return_tensors="pt")

with torch.no_grad():
    logits = model(**inputs).logits

predicted_label = logits.argmax(-1).item()
print(model.config.id2label[predicted_label])""",
        "citation": """
@misc{liu2022convnext,
  title = {A ConvNet for the 2020s},
  author = {Liu, Zhuang and Mao, Hanzi and Wu, Chao-Yuan and Feichtenhofer, Christoph and Darrell, Trevor and Xie, Saining},
  year = {2022},
  archivePrefix = {arXiv},
  eprint = {2201.03545},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2201.03545}
}""",
        "task_type": "image-classification",
    },
    "regnet-y-040": {
        "model_parameters": "21M",
        "model_architecture": "RegNet is designed through Neural Architecture Search (NAS) using a novel design space exploration methodology. RegNet-Y variant includes Squeeze-and-Excitation blocks for improved feature recalibration. Uses quantized linear function to parameterize network widths and depths. The '040' designation refers to 4.0 GFLOPs computational budget.",
        "training_data_sources": "ImageNet-1k",
        "huggingface_url": "https://huggingface.co/facebook/regnet-y-040",
        "input_modalities": ["image"],
        "image_size": "224x224",
        "dependent_packages": ["transformers", "torch", "datasets"],
        "code": """from transformers import AutoImageProcessor, RegNetForImageClassification
import torch
from datasets import load_dataset

dataset = load_dataset("huggingface/cats-image")
image = dataset["test"]["image"][0]

image_processor = AutoImageProcessor.from_pretrained("facebook/regnet-y-040")
model = RegNetForImageClassification.from_pretrained("facebook/regnet-y-040")

inputs = image_processor(image, return_tensors="pt")

with torch.no_grad():
    logits = model(**inputs).logits

predicted_label = logits.argmax(-1).item()
print(model.config.id2label[predicted_label])""",
        "citation": """
@misc{radosavovic2020regnet,
  title = {Designing Network Design Spaces},
  author = {Radosavovic, Ilija and Kosaraju, Raj Prateek and Girshick, Ross and He, Kaiming and Dollar, Piotr},
  year = {2020},
  archivePrefix = {arXiv},
  eprint = {2003.13678},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2003.13678}
}""",
        "task_type": "image-classification",
    },
    "mobilenet-v2": {
        "model_parameters": "3.47M",
        "model_architecture": "Inverted residual structure with linear bottlenecks. Uses depthwise separable convolutions with expansion layers before and projection (bottleneck) layers after. Contains 19 residual bottleneck layers with ReLU6 activation.",
        "training_data_sources": "ImageNet-1k dataset (1 million images, 1,000 classes)",
        "huggingface_url": "https://huggingface.co/google/mobilenet_v2_1.0_224",
        "input_modalities": ["image"],
        "image_size": "224x224",
        "dependent_packages": ["transformers", "PIL", "requests", "torch"],
        "code": """from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import requests

url = "http://images.cocodataset.org/val2017/000000039769.jpg"
image = Image.open(requests.get(url, stream=True).raw)

preprocessor = AutoImageProcessor.from_pretrained("google/mobilenet_v2_1.0_224")
model = AutoModelForImageClassification.from_pretrained("google/mobilenet_v2_1.0_224")

inputs = preprocessor(images=image, return_tensors="pt")
outputs = model(**inputs)
logits = outputs.logits

predicted_class_idx = logits.argmax(-1).item()
print("Predicted class:", model.config.id2label[predicted_class_idx])""",
        "citation": """
@misc{sandler2018mobilenetv2,
  title = {MobileNetV2: Inverted Residuals and Linear Bottlenecks},
  author = {Sandler, Mark and Howard, Andrew and Zhu, Menglong and Zhmoginov, Andrey and Chen, Liang-Chieh},
  year = {2018},
  archivePrefix = {arXiv},
  eprint = {1801.04381},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/1801.04381}
}""",
        "task_type": "image-classification",
    },
    "densenet-121": {
        "model_parameters": "8.0M",
        "model_architecture": "Densely Connected Convolutional Network with dense blocks where each layer receives feature maps from all preceding layers. Trained with RandAugment recipe (RA). GMACs: 2.9, Activations: 6.9M",
        "training_data_sources": "ImageNet-1k with RandAugment (RA) training procedure from 'ResNet Strikes Back'",
        "huggingface_url": "https://huggingface.co/timm/densenet121.ra_in1k",
        "input_modalities": ["image"],
        "image_size": "224x224 (train), 288x288 (test)",
        "dependent_packages": ["timm", "torch", "PIL", "urllib"],
        "code": """from urllib.request import urlopen
from PIL import Image
import timm
import torch

img = Image.open(urlopen(
    'https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/beignets-task-guide.png'
))

model = timm.create_model('densenet121.ra_in1k', pretrained=True)
model = model.eval()

data_config = timm.data.resolve_model_data_config(model)
transforms = timm.data.create_transform(**data_config, is_training=False)

output = model(transforms(img).unsqueeze(0))
top5_probabilities, top5_class_indices = torch.topk(output.softmax(dim=1) * 100, k=5)""",
        "citation": """
@misc{huang2016densenet,
  title = {Densely Connected Convolutional Networks},
  author = {Huang, Gao and Liu, Zhuang and van der Maaten, Laurens and Weinberger, Kilian Q.},
  year = {2016},
  archivePrefix = {arXiv},
  eprint = {1608.06993},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/1608.06993}
}""",
        "task_type": "image-classification",
    },
    "mobilevit-small": {
        "model_parameters": "6.0M",
        "model_architecture": "Hybrid CNN-Transformer architecture combining MobileNetV2-style layers with MobileViT blocks. Replaces local processing in convolutions with global processing using transformers. Image data is converted into flattened patches, processed by transformer layers, then unflattened back into feature maps.",
        "training_data_sources": "ImageNet-1k, trained for 300 epochs with multi-scale sampling (160x160 to 320x320)",
        "huggingface_url": "https://huggingface.co/apple/mobilevit-small",
        "input_modalities": ["image"],
        "image_size": "256x256 (inference), multi-scale training",
        "dependent_packages": ["transformers", "PIL", "requests", "torch"],
        "code": """from transformers import MobileViTFeatureExtractor, MobileViTForImageClassification
from PIL import Image
import requests

url = "http://images.cocodataset.org/val2017/000000039769.jpg"
image = Image.open(requests.get(url, stream=True).raw)

feature_extractor = MobileViTFeatureExtractor.from_pretrained("apple/mobilevit-small")
model = MobileViTForImageClassification.from_pretrained("apple/mobilevit-small")

inputs = feature_extractor(images=image, return_tensors="pt")
outputs = model(**inputs)
logits = outputs.logits

predicted_class_idx = logits.argmax(-1).item()
print("Predicted class:", model.config.id2label[predicted_class_idx])""",
        "citation": """
@misc{mehta2021mobilevit,
  title = {MobileViT: Light-weight, General-purpose, and Mobile-friendly Vision Transformer},
  author = {Mehta, Sachin and Rastegari, Mohammad},
  year = {2021},
  archivePrefix = {arXiv},
  eprint = {2110.02178},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2110.02178}
}""",
        "task_type": "image-classification",
    },
    "efficientformer-l1": {
        "model_parameters": "12.3M",
        "model_architecture": "Efficient Vision Transformer designed for mobile devices with extremely low latency. Uses dimension-consistent design and 4D blocks with CONV-BN fusion. Achieves MobileNet-speed with better accuracy. GMACs: 1.3",
        "training_data_sources": "ImageNet-1k, trained for 1000 epochs on NVIDIA A100 and V100 GPUs",
        "huggingface_url": "https://huggingface.co/snap-research/efficientformer-l1-300",
        "input_modalities": ["image"],
        "image_size": "224x224",
        "dependent_packages": ["transformers", "torch", "PIL", "requests"],
        "code": """import requests
import torch
from PIL import Image
from transformers import EfficientFormerImageProcessor, EfficientFormerForImageClassificationWithTeacher

url = "http://images.cocodataset.org/val2017/000000039769.jpg"
image = Image.open(requests.get(url, stream=True).raw)

model_name = "snap-research/efficientformer-l1-300"
processor = EfficientFormerImageProcessor.from_pretrained(model_name)
model = EfficientFormerForImageClassificationWithTeacher.from_pretrained(model_name)

inputs = processor(images=image, return_tensors="pt")

with torch.no_grad():
    outputs = model(**inputs)

logits = outputs.logits
scores = torch.nn.functional.softmax(logits, dim=1)
top_pred_class = torch.argmax(scores, dim=1)
print(f"Predicted class: {top_pred_class}")""",
        "citation": """
@misc{li2022efficientformer,
  title = {EfficientFormer: Vision Transformers at MobileNet Speed},
  author = {Li, Yanyu and Yuan, Geng and Wen, Yang and Hu, Ju and Evangelidis, Georgios and Tulyakov, Sergey and Wang, Yanzhi and Ren, Jian},
  year = {2022},
  archivePrefix = {arXiv},
  eprint = {2206.01191},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2206.01191}
}""",
        "task_type": "image-classification",
    },
    "swin-base": {
        "model_parameters": "88M",
        "model_architecture": "Hierarchical Vision Transformer using shifted windows. Builds hierarchical feature maps by merging image patches in deeper layers with linear computational complexity. Uses patch size of 4x4 and window size of 7x7",
        "training_data_sources": "ImageNet-1K",
        "huggingface_url": "https://huggingface.co/microsoft/swin-base-patch4-window7-224",
        "input_modalities": ["image"],
        "image_size": "224x224",
        "dependent_packages": ["transformers", "PIL", "requests", "torch"],
        "code": """from transformers import AutoFeatureExtractor, SwinForImageClassification
from PIL import Image
import requests

url = "http://images.cocodataset.org/val2017/000000039769.jpg"
image = Image.open(requests.get(url, stream=True).raw)

feature_extractor = AutoFeatureExtractor.from_pretrained("microsoft/swin-base-patch4-window7-224")
model = SwinForImageClassification.from_pretrained("microsoft/swin-base-patch4-window7-224")

inputs = feature_extractor(images=image, return_tensors="pt")
outputs = model(**inputs)
logits = outputs.logits

predicted_class_idx = logits.argmax(-1).item()
print("Predicted class:", model.config.id2label[predicted_class_idx])""",
        "citation": """
@misc{liu2021swin,
  title = {Swin Transformer: Hierarchical Vision Transformer using Shifted Windows},
  author = {Liu, Ze and Lin, Yutong and Cao, Yue and Hu, Han and Wei, Yixuan and Zhang, Zheng and Lin, Stephen and Guo, Baining},
  year = {2021},
  archivePrefix = {arXiv},
  eprint = {2103.14030},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2103.14030}
}""",
        "task_type": "image-classification",
    },
    # ========================================
    # Embedding Models
    # ========================================
    "dinov2-base": {
        "model_parameters": "86.6M",
        "model_architecture": "Vision Transformer (ViT) trained using self-supervised DINOv2 method. Images presented as sequence of fixed-size patches with [CLS] token and absolute position embeddings. Self-distillation with no labels",
        "training_data_sources": "LVD-142M (curated dataset of 142M images from web sources, ImageNet-22k, ImageNet-1K, Google Landmarks, and fine-grained datasets)",
        "huggingface_url": "https://huggingface.co/facebook/dinov2-base",
        "input_modalities": ["image"],
        "image_size": "224x224 (default), supports up to 518x518",
        "dependent_packages": ["transformers", "PIL", "requests", "torch"],
        "code": """from transformers import AutoImageProcessor, AutoModel
from PIL import Image
import requests

url = 'http://images.cocodataset.org/val2017/000000039769.jpg'
image = Image.open(requests.get(url, stream=True).raw)

processor = AutoImageProcessor.from_pretrained('facebook/dinov2-base')
model = AutoModel.from_pretrained('facebook/dinov2-base')

inputs = processor(images=image, return_tensors="pt")
outputs = model(**inputs)
last_hidden_states = outputs.last_hidden_state""",
        "citation": """
@misc{oquab2023dinov2,
  title = {DINOv2: Learning Robust Visual Features without Supervision},
  author = {Oquab, Maxime and Darcet, Timothee and Moutakanni, Theo and Vo, Huy and Szafraniec, Marc and Khalidov, Vasil and Fernandez, Pierre and Haziza, Daniel and Massa, Francisco and El-Nouby, Alaaeldin and Assran, Mahmoud and Ballas, Nicolas and Galuba, Wojciech and Howes, Russell and Huang, Po-Yao and Li, Shang-Wen and Misra, Ishan and Rabbat, Michael and Sharma, Vasu and Synnaeve, Gabriel and Xu, Hu and Jegou, Herve and Mairal, Julien and Labatut, Patrick and Joulin, Armand and Bojanowski, Piotr},
  year = {2023},
  archivePrefix = {arXiv},
  eprint = {2304.07193},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2304.07193}
}""",
        "pretrained_dataset": "LVD-142M",
        "task_type": "image-embeddings",
    },
    # ========================================
    # Object Detection
    # ========================================
    "detr-resnet-50": {
        "model_parameters": "41.6M",
        "model_architecture": "Encoder-decoder transformer with ResNet-50 convolutional backbone. Features CNN backbone (ResNet-50) for 2D feature extraction, Transformer encoder with 6 layers, width 256, 8 attention heads, Transformer decoder with 6 layers, two detection heads: linear layer for class labels, MLP for bounding boxes, 100 object queries for parallel object detection, bipartite matching loss with Hungarian algorithm",
        "training_data_sources": "COCO 2017 object detection dataset (118k training images, 5k validation images)",
        "huggingface_url": "https://huggingface.co/facebook/detr-resnet-50",
        "input_modalities": ["image"],
        "image_size": "Shortest side ≥ 800px, longest side ≤ 1333px",
        "dependent_packages": ["transformers", "torch", "PIL", "requests"],
        "code": """from transformers import DetrImageProcessor, DetrForObjectDetection
import torch
from PIL import Image
import requests

url = "http://images.cocodataset.org/val2017/000000039769.jpg"
image = Image.open(requests.get(url, stream=True).raw)

processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50", revision="no_timm")
model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50", revision="no_timm")

inputs = processor(images=image, return_tensors="pt")
outputs = model(**inputs)

target_sizes = torch.tensor([image.size[::-1]])
results = processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.9)[0]

for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
    box = [round(i, 2) for i in box.tolist()]
    print(f"Detected {model.config.id2label[label.item()]} with confidence {round(score.item(), 3)} at location {box}")""",
        "citation": """
@misc{carion2020detr,
  title = {End-to-End Object Detection with Transformers},
  author = {Carion, Nicolas and Massa, Francisco and Synnaeve, Gabriel and Usunier, Nicolas and Kirillov, Alexander and Zagoruyko, Sergey},
  year = {2020},
  archivePrefix = {arXiv},
  eprint = {2005.12872},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2005.12872}
}""",
        "pretrained_dataset": "ImageNet (for ResNet-50 backbone)",
        "task_type": "object-detection",
    },
    "yolos-tiny": {
        "model_parameters": "6.2M",
        "model_architecture": "Vision Transformer (ViT) adapted for object detection with DETR-style loss. Features ViT tiny-sized encoder (pretrained on ImageNet), no convolutional backbone, patch-based image processing, 100 object queries, bipartite matching loss (same as DETR), Transformer encoder-only with detection heads. NOTE: This is YOLOS (You Only Look at One Sequence), not YOLOX.",
        "training_data_sources": "Pre-trained on ImageNet-1k (200 epochs), fine-tuned on COCO 2017 object detection (300 epochs)",
        "huggingface_url": "https://huggingface.co/hustvl/yolos-tiny",
        "input_modalities": ["image"],
        "image_size": "Variable (patch-based processing)",
        "dependent_packages": ["transformers", "torch", "PIL", "requests"],
        "code": """from transformers import YolosImageProcessor, YolosForObjectDetection
from PIL import Image
import torch
import requests

url = "http://images.cocodataset.org/val2017/000000039769.jpg"
image = Image.open(requests.get(url, stream=True).raw)

model = YolosForObjectDetection.from_pretrained('hustvl/yolos-tiny')
image_processor = YolosImageProcessor.from_pretrained("hustvl/yolos-tiny")

inputs = image_processor(images=image, return_tensors="pt")
outputs = model(**inputs)

logits = outputs.logits
bboxes = outputs.pred_boxes

target_sizes = torch.tensor([image.size[::-1]])
results = image_processor.post_process_object_detection(outputs, threshold=0.9, target_sizes=target_sizes)[0]

for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
    box = [round(i, 2) for i in box.tolist()]
    print(f"Detected {model.config.id2label[label.item()]} with confidence {round(score.item(), 3)} at location {box}")""",
        "citation": """
@misc{fang2021yolos,
  title = {You Only Look at One Sequence: Rethinking Transformer in Vision through Object Detection},
  author = {Fang, Yuxin and Liao, Bencheng and Wang, Xinggang and Fang, Jiemin and Qi, Jiyang and Wu, Rui and Niu, Jianwei and Liu, Wenyu},
  year = {2021},
  archivePrefix = {arXiv},
  eprint = {2106.00666},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2106.00666}
}""",
        "task_type": "object-detection",
    },
    # ========================================
    # Semantic / Instance / Panoptic Segmentation
    # ========================================
    "segformer-b0": {
        "model_parameters": "3.8M",
        "model_architecture": "Hierarchical Transformer encoder (MiT-B0) with lightweight All-MLP decoder. Mix Transformer (MiT) encoder with 4 stages, hierarchical structure outputting multi-scale features, no positional encoding (uses Mix-FFN instead), efficient self-attention with reduction ratios [64, 16, 4, 1]",
        "training_data_sources": "Pre-trained on ImageNet-1k, fine-tuned on ADE20K dataset at 512x512 resolution",
        "huggingface_url": "https://huggingface.co/nvidia/segformer-b0-finetuned-ade-512-512",
        "input_modalities": ["image"],
        "image_size": "512x512",
        "dependent_packages": ["transformers", "torch", "PIL", "requests"],
        "code": """from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
from PIL import Image
import requests

processor = SegformerImageProcessor.from_pretrained("nvidia/segformer-b0-finetuned-ade-512-512")
model = SegformerForSemanticSegmentation.from_pretrained("nvidia/segformer-b0-finetuned-ade-512-512")

url = "http://images.cocodataset.org/val2017/000000039769.jpg"
image = Image.open(requests.get(url, stream=True).raw)

inputs = processor(images=image, return_tensors="pt")
outputs = model(**inputs)
logits = outputs.logits""",
        "citation": """
@misc{xie2021segformer,
  title = {SegFormer: Simple and Efficient Design for Semantic Segmentation with Transformers},
  author = {Xie, Enze and Wang, Wenhai and Yu, Zhiding and Anandkumar, Anima and Alvarez, Jose M. and Luo, Ping},
  year = {2021},
  archivePrefix = {arXiv},
  eprint = {2105.15203},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2105.15203}
}""",
        "task_type": "segmentation",
    },
    "mask2former-swin": {
        "model_parameters": "102M",
        "model_architecture": "Universal segmentation architecture with Swin Transformer backbone. Features Swin-Base hierarchical vision transformer backbone, multi-scale deformable attention Transformer pixel decoder, Transformer decoder with masked attention, 100 object queries, predicts masks and labels for instance, semantic, and panoptic segmentation",
        "training_data_sources": "COCO 2017 panoptic segmentation dataset",
        "huggingface_url": "https://huggingface.co/facebook/mask2former-swin-base-coco-panoptic",
        "input_modalities": ["image"],
        "image_size": "Variable (typically 1024x1024)",
        "dependent_packages": ["transformers", "torch", "PIL", "requests"],
        "code": """import requests
import torch
from PIL import Image
from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation

processor = AutoImageProcessor.from_pretrained("facebook/mask2former-swin-base-coco-panoptic")
model = Mask2FormerForUniversalSegmentation.from_pretrained("facebook/mask2former-swin-base-coco-panoptic")

url = "http://images.cocodataset.org/val2017/000000039769.jpg"
image = Image.open(requests.get(url, stream=True).raw)

inputs = processor(images=image, return_tensors="pt")

with torch.no_grad():
    outputs = model(**inputs)

class_queries_logits = outputs.class_queries_logits
masks_queries_logits = outputs.masks_queries_logits

result = processor.post_process_panoptic_segmentation(outputs, target_sizes=[image.size[::-1]])[0]
predicted_panoptic_map = result["segmentation"]""",
        "citation": """
@misc{cheng2021mask2former,
  title = {Masked-attention Mask Transformer for Universal Image Segmentation},
  author = {Cheng, Bowen and Misra, Ishan and Schwing, Alexander G. and Kirillov, Alexander and Girdhar, Rohit},
  year = {2021},
  archivePrefix = {arXiv},
  eprint = {2112.01527},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2112.01527}
}""",
        "task_type": "segmentation",
    },
}
