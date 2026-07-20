# Curated dataset registry — vision / image_recognition. Part of the shared
# domain>category taxonomy across resources/{libraries,models,datasets}.
# HuggingFace dataset IDs and arXiv citations are verified on entry;
# use search_huggingface_hub for un-curated needs.
IMAGE_RECOGNITION_DATASETS: dict = {
    "MNIST": {
        "description": "The MNIST database contains 70,000 grayscale images of handwritten digits (0-9). It is a subset of a larger set from NIST, normalized to 28x28 pixels. It is one of the most widely used datasets for training and testing machine learning algorithms for image classification.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/ylecun/mnist",
        "dependent_packages": ["datasets", "PIL", "numpy"],
        "code": """from datasets import load_dataset

# Load MNIST dataset
dataset = load_dataset("ylecun/mnist")

# Access train and test splits
train_data = dataset['train']
test_data = dataset['test']

# Example: Get first image and label
image = train_data[0]['image']
label = train_data[0]['label']
print(f"Label: {label}")

# PyTorch alternative
import torchvision
train_dataset = torchvision.datasets.MNIST(root='./data', train=True, download=True)
""",
        "citation": """@article{lecun1998gradient,
  title={Gradient-based learning applied to document recognition},
  author={LeCun, Yann and Bottou, Léon and Bengio, Yoshua and Haffner, Patrick},
  journal={Proceedings of the IEEE},
  volume={86},
  number={11},
  pages={2278--2324},
  year={1998},
  publisher={IEEE}
}""",
        "num_training_samples": 60000,
        "num_validation_samples": 10000,
        "num_classes": 10,
        "image_size": "28x28 (grayscale)",
        "release_year": 1998,
    },
    "Fashion-MNIST": {
        "description": "Fashion-MNIST is a dataset of Zalando's article images, consisting of 70,000 grayscale images in 10 categories. It was created as a direct drop-in replacement for MNIST with the same image size and structure, but provides a more challenging classification task.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/zalando-datasets/fashion_mnist",
        "dependent_packages": ["datasets", "PIL", "numpy"],
        "code": """from datasets import load_dataset

# Load Fashion-MNIST dataset
dataset = load_dataset("zalando-datasets/fashion_mnist")

# Access splits
train_data = dataset['train']
test_data = dataset['test']

# Class labels: 0=T-shirt/top, 1=Trouser, 2=Pullover, 3=Dress, 4=Coat,
#               5=Sandal, 6=Shirt, 7=Sneaker, 8=Bag, 9=Ankle boot

# PyTorch alternative
import torchvision
train_dataset = torchvision.datasets.FashionMNIST(root='./data', train=True, download=True)
""",
        "citation": """@article{xiao2017fashion,
  title={Fashion-MNIST: a Novel Image Dataset for Benchmarking Machine Learning Algorithms},
  author={Xiao, Han and Rasul, Kashif and Vollgraf, Roland},
  journal={arXiv preprint arXiv:1708.07747},
  year={2017}
}""",
        "num_training_samples": 60000,
        "num_validation_samples": 10000,
        "num_classes": 10,
        "image_size": "28x28 (grayscale)",
        "release_year": 2017,
    },
    "CIFAR-100": {
        "description": "CIFAR-100 is a dataset containing 60,000 32x32 color images in 100 classes, with 600 images per class. The 100 classes are grouped into 20 superclasses. Each image comes with a fine label (the class) and a coarse label (the superclass).",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/uoft-cs/cifar100",
        "dependent_packages": ["datasets", "PIL", "numpy"],
        "code": """from datasets import load_dataset

# Load CIFAR-100 dataset
dataset = load_dataset("uoft-cs/cifar100")

# Access splits
train_data = dataset['train']
test_data = dataset['test']

# Each sample has 'fine_label' (0-99) and 'coarse_label' (0-19)
image = train_data[0]['img']
fine_label = train_data[0]['fine_label']
coarse_label = train_data[0]['coarse_label']

# PyTorch alternative
import torchvision
train_dataset = torchvision.datasets.CIFAR100(root='./data', train=True, download=True)
""",
        "citation": """@techreport{krizhevsky2009learning,
  title={Learning multiple layers of features from tiny images},
  author={Krizhevsky, Alex and Hinton, Geoffrey},
  institution={University of Toronto},
  year={2009}
}""",
        "num_training_samples": 50000,
        "num_validation_samples": 10000,
        "num_classes": "100 (+ 20 superclasses)",
        "image_size": "32x32 (RGB)",
        "release_year": 2009,
    },
    "COCO": {
        "description": "Microsoft COCO (Common Objects in Context) is a large-scale object detection, segmentation, and captioning dataset. It contains 330K images with over 200K labeled images. Images contain complex everyday scenes with common objects in their natural context.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["object-detection", "instance-segmentation", "image-captioning"],
        "huggingface_url": "https://huggingface.co/datasets/detection-datasets/coco",
        "dependent_packages": ["datasets", "pycocotools", "PIL"],
        "code": """from datasets import load_dataset

# Load COCO 2017 dataset
dataset = load_dataset("detection-datasets/coco")

# Access splits
train_data = dataset['train']
val_data = dataset['validation']

# Each sample contains image, objects (bboxes, labels, segmentation masks)
sample = train_data[0]
image = sample['image']
objects = sample['objects']
bboxes = objects['bbox']
category_ids = objects['category_id']

# Alternative: using official COCO API
from pycocotools.coco import COCO
coco = COCO('path/to/annotations/instances_train2017.json')
""",
        "citation": """@inproceedings{lin2014microsoft,
  title={Microsoft COCO: Common objects in context},
  author={Lin, Tsung-Yi and Maire, Michael and Belongie, Serge and Hays, James and Perona, Pietro and Ramanan, Deva and Dollár, Piotr and Zitnick, C Lawrence},
  booktitle={European Conference on Computer Vision},
  pages={740--755},
  year={2014},
  organization={Springer}
}""",
        "num_training_samples": 118287,
        "num_validation_samples": 5000,
        "num_classes": 80,
        "image_size": "variable",
        "release_year": 2014,
    },
    "Pascal-VOC": {
        "description": "The PASCAL Visual Object Classes (VOC) dataset is a well-known benchmark for object detection, semantic segmentation, and classification. It contains 20 object categories with detailed annotations including bounding boxes, class labels, and segmentation masks.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": [
            "object-detection",
            "semantic-segmentation",
            "image-classification",
        ],
        "huggingface_url": "https://huggingface.co/datasets/merve/pascal-voc",
        "dependent_packages": ["datasets", "PIL", "xml"],
        "code": """from datasets import load_dataset

# Load Pascal VOC dataset
dataset = load_dataset("merve/pascal-voc", "2012")

# Access data
train_data = dataset['train']

# Each sample contains image and objects with bounding boxes
sample = train_data[0]
image = sample['image']
objects = sample['objects']
bboxes = objects['bbox']
labels = objects['label']

# PyTorch alternative
import torchvision
train_dataset = torchvision.datasets.VOCDetection(root='./data', year='2012',
                                                   image_set='train', download=True)
""",
        "citation": """@article{everingham2010pascal,
  title={The Pascal Visual Object Classes (VOC) challenge},
  author={Everingham, Mark and Van Gool, Luc and Williams, Christopher KI and Winn, John and Zisserman, Andrew},
  journal={International Journal of Computer Vision},
  volume={88},
  number={2},
  pages={303--338},
  year={2010}
}""",
        "num_training_samples": 16551,
        "num_validation_samples": 4952,
        "num_classes": 20,
        "image_size": "variable",
        "release_year": 2012,
    },
    "SVHN": {
        "description": "The Street View House Numbers (SVHN) dataset is obtained from house numbers in Google Street View images. It contains over 600,000 digit images and is similar to MNIST but incorporates the challenging problem of recognizing digits in natural scene images.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/ufldl-stanford/svhn",
        "dependent_packages": ["datasets", "PIL", "numpy"],
        "code": """from datasets import load_dataset

# Load SVHN dataset (cropped digits format)
dataset = load_dataset("ufldl-stanford/svhn", "cropped_digits")

# Access splits
train_data = dataset['train']
test_data = dataset['test']
extra_data = dataset['extra']  # Additional 531,131 images

# Each sample contains RGB image and digit label (0-9)
image = train_data[0]['image']
label = train_data[0]['label']

# PyTorch alternative
import torchvision
train_dataset = torchvision.datasets.SVHN(root='./data', split='train', download=True)
""",
        "citation": """@inproceedings{netzer2011reading,
  title={Reading digits in natural images with unsupervised feature learning},
  author={Netzer, Yuval and Wang, Tao and Coates, Adam and Bissacco, Alessandro and Wu, Bo and Ng, Andrew Y},
  booktitle={NIPS Workshop on Deep Learning and Unsupervised Feature Learning},
  year={2011}
}""",
        "num_training_samples": 73257,
        "num_validation_samples": 26032,
        "num_classes": 10,
        "image_size": "32x32 (RGB)",
        "release_year": 2011,
    },
    "Food-101": {
        "description": "Food-101 is a challenging dataset of 101,000 food images organized into 101 food categories. Each category contains 1,000 images. The training images were not cleaned and thus contain some noise. The test images are manually reviewed and cleaned.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/ethz/food101",
        "dependent_packages": ["datasets", "PIL"],
        "code": """from datasets import load_dataset

# Load Food-101 dataset
dataset = load_dataset("ethz/food101")

# Access splits
train_data = dataset['train']
test_data = dataset['validation']  # Note: 'validation' is actually the test set

# Each sample contains image and label (0-100)
image = train_data[0]['image']
label = train_data[0]['label']

# TensorFlow alternative
import tensorflow_datasets as tfds
dataset = tfds.load('food101', split='train')
""",
        "citation": """@inproceedings{bossard2014food,
  title={Food-101 -- Mining Discriminative Components with Random Forests},
  author={Bossard, Lukas and Guillaumin, Matthieu and Van Gool, Luc},
  booktitle={European Conference on Computer Vision},
  year={2014}
}""",
        "num_training_samples": 75750,
        "num_validation_samples": 25250,
        "num_classes": 101,
        "image_size": "512px (max side)",
        "release_year": 2014,
    },
    "Oxford-Flowers-102": {
        "description": "Oxford Flowers 102 is a fine-grained classification dataset consisting of 102 flower categories commonly found in the UK. Each class contains between 40 and 258 images with large scale, pose and light variations.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/Voxel51/OxfordFlowers102",
        "dependent_packages": ["datasets", "PIL"],
        "code": """from datasets import load_dataset

# Load Oxford Flowers 102 dataset
dataset = load_dataset("Voxel51/OxfordFlowers102")

# Access splits
train_data = dataset['train']
val_data = dataset['validation']
test_data = dataset['test']

# Each sample contains image and label (0-101)
image = train_data[0]['image']
label = train_data[0]['label']

# PyTorch alternative
import torchvision
train_dataset = torchvision.datasets.Flowers102(root='./data', split='train', download=True)
""",
        "citation": """@InProceedings{Nilsback08,
  author = {Nilsback, M-E. and Zisserman, A.},
  title = {Automated Flower Classification over a Large Number of Classes},
  booktitle = {Proceedings of the Indian Conference on Computer Vision, Graphics and Image Processing},
  year = {2008}
}""",
        "num_training_samples": 1020,
        "num_validation_samples": 1020,
        "num_classes": 102,
        "image_size": "variable",
        "release_year": 2008,
    },
    "STL-10": {
        "description": "An image recognition dataset inspired by CIFAR-10 but designed specifically for developing unsupervised feature learning, deep learning, and self-taught learning algorithms. Each class has fewer labeled training examples than CIFAR-10, but includes 100,000 unlabeled images for unsupervised pre-training.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/tanganke/stl10",
        "dependent_packages": ["datasets", "PIL", "numpy", "torch"],
        "code": """from datasets import load_dataset

# Load the STL-10 dataset
dataset = load_dataset('tanganke/stl10')

# Access training and test splits
train_data = dataset['train']
test_data = dataset['test']

# Example: Access first training image
sample = train_data[0]
image = sample['image']  # PIL Image
label = sample['label']  # Integer label (0-9)""",
        "citation": """@techreport{Coates2011,
  author = {Adam Coates and Honglak Lee and Andrew Y. Ng},
  title = {An Analysis of Single Layer Networks in Unsupervised Feature Learning},
  institution = {Stanford University},
  year = {2011}
}""",
        "num_training_samples": 5000,
        "num_validation_samples": 8000,
        "num_classes": 10,
        "image_size": "96x96 (RGB)",
        "release_year": 2011,
    },
    "Caltech-101": {
        "description": "Caltech-101 contains pictures of objects belonging to 101 categories plus a background category. Each category contains roughly 40 to 800 images. The dataset was collected to test object recognition methods and computer vision techniques.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["object-detection"],
        "huggingface_url": "https://huggingface.co/datasets/flwrlabs/caltech101",
        "dependent_packages": ["datasets", "PIL"],
        "code": """from datasets import load_dataset

# Load Caltech-101 dataset
dataset = load_dataset("flwrlabs/caltech101")

# Access data (no official train/test split)
data = dataset['train']

# Each sample contains image and label (0-100)
image = data[0]['image']
label = data[0]['label']

# Common practice: split manually
from sklearn.model_selection import train_test_split
# Use 30 images per class for training, rest for testing

# PyTorch alternative
import torchvision
dataset = torchvision.datasets.Caltech101(root='./data', download=True)
""",
        "citation": """@article{fei2006one,
  title={One-shot learning of object categories},
  author={Fei-Fei, Li and Fergus, Rob and Perona, Pietro},
  journal={IEEE Transactions on Pattern Analysis and Machine Intelligence},
  volume={28},
  number={4},
  pages={594--611},
  year={2006},
  publisher={IEEE}
}""",
        "num_training_samples": 8677,
        "num_validation_samples": 0,
        "num_classes": 101,
        "image_size": "variable (approx. 300x200)",
        "release_year": 2006,
    },
    "ADE20K": {
        "description": "Large-scale dataset for semantic segmentation and scene parsing. Contains 27,574 images with comprehensive pixel-level annotations covering 3,688 object categories. MIT Scene Parsing Benchmark uses 150-class subset.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["semantic-segmentation", "instance-segmentation"],
        "huggingface_url": "https://huggingface.co/datasets/scene_parse_150",
        "dependent_packages": ["datasets", "transformers", "pillow", "numpy", "torch"],
        "code": """from datasets import load_dataset

# Load ADE20K (150-class benchmark)
dataset = load_dataset("scene_parse_150")

train_dataset = dataset['train']
val_dataset = dataset['validation']

sample = train_dataset[0]
image = sample['image']
annotation = sample['annotation']
scene_category = sample['scene_category']

# Using with transformers for semantic segmentation
from transformers import BeitFeatureExtractor, BeitForSemanticSegmentation

feature_extractor = BeitFeatureExtractor.from_pretrained(
    'microsoft/beit-base-finetuned-ade-640-640'
)
model = BeitForSemanticSegmentation.from_pretrained(
    'microsoft/beit-base-finetuned-ade-640-640'
)

inputs = feature_extractor(images=image, return_tensors="pt")
outputs = model(**inputs)
logits = outputs.logits
""",
        "citation": """@inproceedings{zhou2017scene,
  title={Scene Parsing through ADE20K Dataset},
  author={Zhou, Bolei and Zhao, Hang and Puig, Xavier and Fidler, Sanja and Barriuso, Adela and Torralba, Antonio},
  booktitle={Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)},
  year={2017}
}""",
        "num_training_samples": 20210,
        "num_validation_samples": 2000,
        "num_classes": "150 (benchmark) / 3,688 (full)",
        "image_size": "variable, typically 512x683 pixels",
        "release_year": 2017,
    },
    "Cityscapes": {
        "description": "Large-scale benchmark for urban street scene understanding. Contains diverse stereo video sequences from 50 different cities with high-quality pixel-level annotations for semantic, instance, and panoptic segmentation.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": [
            "semantic-segmentation",
            "instance-segmentation",
            "panoptic-segmentation",
        ],
        "huggingface_url": "https://huggingface.co/datasets/Chris1/cityscapes",
        "dependent_packages": [
            "cityscapesscripts",
            "pillow",
            "numpy",
            "torch",
            "torchvision",
        ],
        "code": """from torchvision.datasets import Cityscapes
from torch.utils.data import DataLoader
from torchvision import transforms

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

dataset = Cityscapes(
    root='./data/cityscapes',
    split='train',
    mode='fine',
    target_type='semantic',
    transform=transform
)

train_loader = DataLoader(dataset, batch_size=4, shuffle=True, num_workers=4)

# For multiple target types
dataset_multi = Cityscapes(
    root='./data/cityscapes',
    split='train',
    mode='fine',
    target_type=['instance', 'semantic', 'color']
)
""",
        "citation": """@inproceedings{Cordts2016Cityscapes,
  title={The Cityscapes Dataset for Semantic Urban Scene Understanding},
  author={Cordts, Marius and Omran, Mohamed and Ramos, Sebastian and Rehfeld, Timo and Enzweiler, Markus and Benenson, Rodrigo and Franke, Uwe and Roth, Stefan and Schiele, Bernt},
  booktitle={Proc. of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)},
  year={2016}
}""",
        "num_training_samples": 2975,
        "num_validation_samples": 500,
        "num_classes": "30 classes (19 evaluation classes)",
        "image_size": "1024x2048 pixels",
        "release_year": 2016,
    },
    "Oxford-IIIT-Pet": {
        "description": "Dataset of 37 pet breeds (cats and dogs) with ~7,349 images. Each image has breed annotation, head bounding box, and pixel-level foreground-background segmentation (trimap). Ideal for fine-grained classification.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification", "semantic-segmentation"],
        "huggingface_url": "https://huggingface.co/datasets/timm/oxford-iiit-pet",
        "dependent_packages": ["torch", "torchvision", "pillow", "datasets", "numpy"],
        "code": """from datasets import load_dataset

# Hugging Face Datasets
dataset = load_dataset("timm/oxford-iiit-pet")

train_data = dataset['train']
test_data = dataset['test']

example = train_data[0]
image = example['image']
label = example['label']

# PyTorch alternative
import torchvision
from torchvision import transforms

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

train_dataset = torchvision.datasets.OxfordIIITPet(
    root='./data',
    split='trainval',
    target_types='category',
    transform=transform,
    download=True
)
""",
        "citation": """@InProceedings{parkhi12a,
  author    = "Parkhi, O. M. and Vedaldi, A. and Zisserman, A. and Jawahar, C.~V.",
  title     = "Cats and Dogs",
  booktitle = "IEEE Conference on Computer Vision and Pattern Recognition",
  year      = "2012",
}""",
        "num_training_samples": 3680,
        "num_validation_samples": 3669,
        "num_classes": 37,
        "image_size": "variable, typically resized to 224x224 or 256x256",
        "release_year": 2012,
    },
    "Stanford-Dogs": {
        "description": "The Stanford Dogs dataset contains images of 120 breeds of dogs from around the world. This dataset has been built using images and annotation from ImageNet for the task of fine-grained image categorization. Designed for fine-grained visual recognition with minimal inter-class variation between similar dog breeds.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/Alanox/stanford-dogs",
        "dependent_packages": ["datasets", "PIL", "Python"],
        "code": """from datasets import load_dataset

# Load the dataset
dataset = load_dataset("Alanox/stanford-dogs", split="full")

# Access a sample
sample = dataset[0]
image = sample['image']
label = sample['target']
annotations = sample['annotations']  # Bounding boxes""",
        "citation": """@inproceedings{KhoslaYaoJayadevaprakashFeiFei_FGVC2011,
    author = {Aditya Khosla and Nityananda Jayadevaprakash and Bangpeng Yao and Li Fei-Fei},
    title = {Novel Dataset for Fine-Grained Image Categorization},
    booktitle = {FGVC Workshop, CVPR},
    year = {2011}
}""",
        "num_training_samples": 12000,
        "num_validation_samples": 8580,
        "num_classes": 120,
        "image_size": "variable (RGB)",
        "release_year": 2011,
    },
    "CUB-200-2011": {
        "description": "Caltech-UCSD Birds-200-2011 dataset with 11,788 images of 200 bird species. Each image has 1 subcategory label, 15 part locations, 312 binary attributes, and 1 bounding box. Fine-grained visual classification benchmark.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/bentrevett/caltech-ucsd-birds-200-2011",
        "dependent_packages": ["torch", "torchvision", "pillow", "pandas", "datasets"],
        "code": """from datasets import load_dataset

# Hugging Face Datasets
dataset = load_dataset("bentrevett/caltech-ucsd-birds-200-2011")

train_data = dataset["train"]
test_data = dataset["test"]

example = train_data[0]
image = example["image"]
label = example["label"]
bbox = example["bbox"]

# Custom PyTorch Dataset
import os
import pandas as pd
from torchvision.datasets import VisionDataset
from torchvision import transforms

class Cub2011(VisionDataset):
    def __init__(self, root, train=True, transform=None):
        super().__init__(root, transform=transform)
        self.train = train
        self._load_metadata()

    def _load_metadata(self):
        images = pd.read_csv(os.path.join(self.root, 'CUB_200_2011', 'images.txt'),
                            sep=' ', names=['img_id', 'filepath'])
        image_class_labels = pd.read_csv(
            os.path.join(self.root, 'CUB_200_2011', 'image_class_labels.txt'),
            sep=' ', names=['img_id', 'target'])
        train_test_split = pd.read_csv(
            os.path.join(self.root, 'CUB_200_2011', 'train_test_split.txt'),
            sep=' ', names=['img_id', 'is_training_img'])

        data = images.merge(image_class_labels, on='img_id')
        self.data = data.merge(train_test_split, on='img_id')

        if self.train:
            self.data = self.data[self.data.is_training_img == 1]
        else:
            self.data = self.data[self.data.is_training_img == 0]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        sample = self.data.iloc[idx]
        path = os.path.join(self.root, 'CUB_200_2011/images', sample.filepath)
        target = sample.target - 1
        image = Image.open(path).convert('RGB')

        if self.transform:
            image = self.transform(image)
        return image, target
""",
        "citation": """@techreport{WahCUB_200_2011,
    Title = {{The Caltech-UCSD Birds-200-2011 Dataset}},
    Author = {Wah, C. and Branson, S. and Welinder, P. and Perona, P. and Belongie, S.},
    Year = {2011},
    Institution = {California Institute of Technology},
    Number = {CNS-TR-2011-001}
}""",
        "num_training_samples": 5994,
        "num_validation_samples": 5794,
        "num_classes": 200,
        "image_size": "variable, typically resized to 224x224, 299x299, or 448x448",
        "release_year": 2011,
    },
    "Caltech-256": {
        "description": "A challenging set of 256 object categories containing a total of 30,607 images. An improvement over Caltech-101 with more than doubled number of categories, increased minimum images per category, and includes a larger clutter category for testing background rejection.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/ilee0022/Caltech-256",
        "dependent_packages": ["datasets", "PIL", "Python"],
        "code": """from datasets import load_dataset

# Load the dataset
dataset = load_dataset("ilee0022/Caltech-256")

# Access an example
example = dataset["train"][0]
image = example["image"]
label = example["label"]
class_name = example["text"]""",
        "citation": """@misc{griffin_holub_perona_2022,
  title={Caltech 256},
  DOI={10.22002/D1.20087},
  publisher={CaltechDATA},
  author={Griffin, Gregory and Holub, Alex and Perona, Pietro},
  year={2022}
}""",
        "num_training_samples": 30607,
        "num_validation_samples": 0,
        "num_classes": 257,
        "image_size": "variable",
        "release_year": 2007,
    },
    "Tiny-ImageNet": {
        "description": "Subset of ImageNet LSVRC created for Stanford CS231n. Contains 200 classes with 64x64 color images. Each class has 500 training images, 50 validation images, and 50 test images. Designed for educational purposes and rapid prototyping.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/zh-plus/tiny-imagenet",
        "dependent_packages": ["datasets", "pillow", "torch", "torchvision", "numpy"],
        "code": """from datasets import load_dataset

# Hugging Face Datasets
tiny_imagenet = load_dataset('zh-plus/tiny-imagenet', split='train')

print(tiny_imagenet[0])
# Output: {'image': <PIL.JpegImagePlugin.JpegImageFile>, 'label': 15}

train_data = load_dataset('zh-plus/tiny-imagenet', split='train')
valid_data = load_dataset('zh-plus/tiny-imagenet', split='valid')

# PyTorch DataLoader integration
from torch.utils.data import DataLoader

tiny_imagenet.set_format(type='torch', columns=['image', 'label'])
train_loader = DataLoader(tiny_imagenet, batch_size=32, shuffle=True)

# Traditional PyTorch ImageFolder (for local data)
from torchvision import datasets, transforms

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

train_dataset = datasets.ImageFolder(
    root='path/to/tiny-imagenet-200/train',
    transform=transform
)

train_loader = torch.utils.data.DataLoader(
    train_dataset,
    batch_size=100,
    shuffle=True,
    num_workers=4
)
""",
        "citation": """@article{le2015tiny,
  title={Tiny ImageNet Visual Recognition Challenge},
  author={Le, Ya and Yang, Xuan S.},
  journal={CS 231N},
  volume={7},
  number={7},
  pages={3},
  year={2015}
}""",
        "num_training_samples": 100000,
        "num_validation_samples": 10000,
        "num_classes": 200,
        "image_size": "64x64 pixels (RGB)",
        "release_year": 2015,
    },
    "FGVC-Aircraft": {
        "description": "A benchmark dataset for fine-grained visual categorization of aircraft. Contains images of aircraft with tight bounding boxes and hierarchical labels organized in four levels: Model, Variant (102 classes), Family (70 classes), and Manufacturer (41 classes).",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/HuggingFaceM4/FGVC-Aircraft",
        "dependent_packages": ["datasets", "matplotlib", "PIL", "numpy"],
        "code": """from datasets import load_dataset
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Load dataset
ds = load_dataset("HuggingFaceM4/FGVC-Aircraft")

# Access training data
train_data = ds["train"]
sample = train_data[0]

# Extract image and bounding box
image = sample["image"]
bbox = sample["bbox"]""",
        "citation": """@techreport{maji13fine-grained,
  title = {Fine-Grained Visual Classification of Aircraft},
  author = {S. Maji and J. Kannala and E. Rahtu and M. Blaschko and A. Vedaldi},
  year = {2013},
  institution = {arXiv},
  number = {arXiv:1306.5151}
}""",
        "num_training_samples": 3400,
        "num_validation_samples": 6800,
        "num_classes": 102,
        "image_size": "variable",
        "release_year": 2013,
    },
    "Omniglot": {
        "description": "One-shot and few-shot learning dataset with 1,623 handwritten characters from 50 alphabets. Each character drawn by 20 people (32,460 total images). Includes stroke data with temporal information.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["few-shot-classification", "one-shot-classification"],
        "huggingface_url": "https://huggingface.co/datasets/GATE-engine/omniglot",
        "dependent_packages": [
            "torch",
            "torchvision",
            "numpy",
            "scipy",
            "PIL",
            "tensorflow-datasets",
            "datasets",
        ],
        "code": """# TensorFlow Datasets
import tensorflow_datasets as tfds
dataset, info = tfds.load('omniglot', with_info=True, as_supervised=True)

# PyTorch torchvision
from torchvision.datasets import Omniglot
import torchvision.transforms as transforms

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

train_dataset = Omniglot(root='./data', background=True,
                         download=True, transform=transform)
test_dataset = Omniglot(root='./data', background=False,
                        download=True, transform=transform)
""",
        "citation": """@article{lake2015human,
  title={Human-level concept learning through probabilistic program induction},
  author={Lake, Brenden M and Salakhutdinov, Ruslan and Tenenbaum, Joshua B},
  journal={Science},
  volume={350},
  number={6266},
  pages={1332--1338},
  year={2015}
}""",
        "num_training_samples": 19280,
        "num_validation_samples": 13180,
        "num_classes": 1623,
        "image_size": "105x105",
        "release_year": 2015,
    },
    "EuroSAT": {
        "description": "A benchmark dataset for land use and land cover classification based on Sentinel-2 satellite imagery. Contains 27,000 labeled and geo-referenced samples covering 10 land use classes across 34 European countries.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/timm/eurosat-rgb",
        "dependent_packages": ["datasets", "PIL", "numpy", "torch"],
        "code": """from datasets import load_dataset

# Load EuroSAT RGB dataset
dataset = load_dataset("timm/eurosat-rgb")

# Access the dataset
all_data = dataset['train']

# Access sample
sample = all_data[0]
image = sample['image']  # PIL Image 64x64
label = sample['label']  # Integer label (0-9)""",
        "citation": """@article{helber2019eurosat,
  title={Eurosat: A novel dataset and deep learning benchmark for land use and land cover classification},
  author={Helber, Patrick and Bischke, Benjamin and Dengel, Andreas and Borth, Damian},
  journal={IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing},
  volume={12},
  number={7},
  pages={2217--2226},
  year={2019},
  publisher={IEEE}
}""",
        "num_training_samples": 21600,
        "num_validation_samples": 5400,
        "num_classes": 10,
        "image_size": "64x64 (RGB)",
        "release_year": 2019,
    },
    "UC-Merced": {
        "description": "The UC Merced Land Use dataset is a land use classification dataset containing 256x256 pixel, 1-foot resolution RGB images of urban locations around the United States extracted from the USGS National Map Urban Area Imagery collection. Consists of 21 land use classes representing different types of land cover.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/blanchon/UC_Merced",
        "dependent_packages": ["datasets", "PIL", "Python"],
        "code": """from datasets import load_dataset

# Load the dataset
UC_Merced = load_dataset("blanchon/UC_Merced")

# Access training split
train_dataset = UC_Merced['train']

# Access a sample
sample = train_dataset[0]
image = sample['image']
label = sample['label']  # Integer label (0-20)""",
        "citation": """@inproceedings{yang2010bag,
    author = {Yang, Yi and Newsam, Shawn},
    title = {Bag-Of-Visual-Words and Spatial Extensions for Land-Use Classification},
    booktitle = {ACM SIGSPATIAL International Conference on Advances in Geographic Information Systems},
    year = {2010},
    pages = {270--279}
}""",
        "num_training_samples": 1680,
        "num_validation_samples": 420,
        "num_classes": 21,
        "image_size": "256x256",
        "release_year": 2010,
    },
    "RESISC45": {
        "description": "RESISC45 (Remote Sensing Image Scene Classification) is a benchmark comprising 31,500 RGB images extracted using Google Earth, with each image having a resolution of 256x256 pixels. Images are collected from over 100 countries with high variability in image conditions.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/timm/resisc45",
        "dependent_packages": ["datasets", "PIL", "Python"],
        "code": """from datasets import load_dataset

# Load the dataset
dataset = load_dataset("timm/resisc45")

# Access training examples
train_example = dataset['train'][0]
print(train_example['image'])
print(train_example['label'])
print(train_example['image_id'])""",
        "citation": """@article{Cheng_2017,
  title={Remote Sensing Image Scene Classification: Benchmark and State of the Art},
  author={Cheng, Gong and Han, Junwei and Lu, Xiaoqiang},
  journal={Proceedings of the IEEE},
  volume={105},
  number={10},
  pages={1865-1883},
  year={2017}
}""",
        "num_training_samples": 18900,
        "num_validation_samples": 12600,
        "num_classes": 45,
        "image_size": "256x256 (RGB)",
        "release_year": 2017,
    },
    "FER2013": {
        "description": "FER-2013: 35,887 48x48 grayscale face images labeled with 7 emotions (angry, disgust, fear, happy, sad, surprise, neutral). Used for facial expression recognition.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification", "facial-expression-recognition"],
        "huggingface_url": "https://huggingface.co/datasets/Jeneral/fer2013",
        "dependent_packages": ["datasets", "numpy"],
        "code": """from datasets import load_dataset
# Load FER2013 dataset
dataset = load_dataset("Jeneral/fer2013")
train_data = dataset['train']
image = train_data[0]['image']
label = train_data[0]['labels']""",
        "citation": """@inproceedings{mollahosseini2016going,
  title={Going deeper in facial expression recognition using deep neural networks},
  author={Mollahosseini, Ahmad and Hasani, Behzad and Mahoor, Mohammad H},
  booktitle={WACV},
  pages={1--10},
  year={2016}
}""",
        "num_training_samples": 28709,
        "num_validation_samples": 3589,
        "num_classes": 7,
        "image_size": "48x48 (grayscale)",
        "release_year": 2013,
    },
    "AffectNet": {
        "description": "AffectNet is one of the largest databases for facial expression, valence, and arousal in the wild. Contains over 1 million facial images collected from the Internet, with approximately 440,000 images manually annotated for 8 discrete facial expressions and continuous values of valence and arousal.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["facial-expression-recognition", "valence-arousal-prediction"],
        "huggingface_url": "https://huggingface.co/datasets/chitradrishti/AffectNet",
        "dependent_packages": [
            "datasets",
            "torch",
            "tensorflow",
            "opencv-python",
            "PIL",
            "numpy",
        ],
        "code": """from datasets import load_dataset
import torch
import torch.nn as nn
from torchvision import transforms

# Load AffectNet dataset
dataset = load_dataset("chitradrishti/AffectNet")

train_data = dataset['train']
val_data = dataset['validation']

# Transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                       std=[0.229, 0.224, 0.225])
])

# Classes: 0=Neutral, 1=Happy, 2=Sad, 3=Surprise,
#          4=Fear, 5=Disgust, 6=Anger, 7=Contempt
# Also includes valence and arousal values (continuous)

sample = train_data[0]
image = sample['image']
expression = sample['expression']
valence = sample['valence']
arousal = sample['arousal']
""",
        "citation": """@article{mollahosseini2017affectnet,
  title={Affectnet: A database for facial expression, valence, and arousal computing in the wild},
  author={Mollahosseini, Ali and Hasani, Behzad and Mahoor, Mohammad H},
  journal={IEEE Transactions on Affective Computing},
  volume={10},
  number={1},
  pages={18--31},
  year={2017}
}""",
        "num_training_samples": 287651,
        "num_validation_samples": 3500,
        "num_classes": 8,
        "image_size": "variable (typically resized to 224x224 or 256x256)",
        "release_year": 2017,
    },
    "WIDER-FACE": {
        "description": "WIDER FACE: a face detection dataset with 32,203 images and 393,703 labeled faces across 61 event classes. Includes high variability in pose, scale, and occlusion.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["face-detection"],
        "huggingface_url": "https://huggingface.co/datasets/zhanghao/FaceDetectionWIDERFACE",
        "dependent_packages": ["torchvision", "PIL"],
        "code": """from torchvision.datasets import WIDERFace
wider_train = WIDERFace(root='./data', split='train', download=True)
image, target = wider_train[0]""",
        "citation": """@inproceedings{yang2016wider,
  title={WIDER FACE: A Face Detection Benchmark},
  author={Yang, Shuo and Luo, Ping and Loy, Chen Change and Tang, Xiaoou},
  booktitle={CVPR},
  pages={5525--5533},
  year={2016}
}""",
        "num_training_samples": 32203,
        "num_validation_samples": 0,
        "num_classes": "N/A (detection)",
        "image_size": "variable",
        "release_year": 2016,
    },
    "VGGFace2": {
        "description": "A large-scale face recognition dataset with 3.31 million images of 9,131 subjects. Downloaded from Google Image Search with large variations in pose, age, illumination, ethnicity, and profession. Widely used for face recognition and face verification tasks.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["face-verification"],
        "huggingface_url": "https://huggingface.co/datasets/ProgramComputer/VGGFace2",
        "dependent_packages": [
            "torch",
            "keras-vggface",
            "tensorflow",
            "opencv-python",
            "PIL",
        ],
        "code": """from keras_vggface.vggface import VGGFace
import numpy as np
from keras_vggface import utils
from keras.preprocessing import image

# Load pre-trained VGGFace2 model
model = VGGFace(
    model='resnet50',
    include_top=True,
    input_shape=(224, 224, 3),
    pooling='avg'
)

# Load and preprocess image
img = image.load_img('path/to/face_image.jpg', target_size=(224, 224))
x = image.img_to_array(img)
x = np.expand_dims(x, axis=0)
x = utils.preprocess_input(x, version=2)  # version=2 for VGGFace2

# Get predictions
preds = model.predict(x)
print(f'Predicted identity: {np.argmax(preds)}')

# For face verification
model_verification = VGGFace(
    model='resnet50',
    include_top=False,
    input_shape=(224, 224, 3),
    pooling='avg'
)
""",
        "citation": """@inproceedings{cao2018vggface2,
  title={Vggface2: A dataset for recognising faces across pose and age},
  author={Cao, Qiong and Shen, Li and Xie, Weidi and Parkhi, Omkar M and Zisserman, Andrew},
  booktitle={13th IEEE International Conference on Automatic Face & Gesture Recognition (FG 2018)},
  pages={67--74},
  year={2018}
}""",
        "num_training_samples": 3141890,
        "num_validation_samples": 169396,
        "num_classes": 9131,
        "image_size": "variable (typically resized to 224x224)",
        "release_year": 2018,
    },
    "DAVIS": {
        "description": "Densely Annotated VIdeo Segmentation benchmark for high-quality video object segmentation. Consists of Full HD resolution video sequences covering challenges like occlusion, motion blur, and appearance changes. Each video frame has pixel-accurate dense annotations.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["video-object-segmentation"],
        "huggingface_url": "https://davischallenge.org/",
        "dependent_packages": ["opencv-python", "numpy", "PIL", "scipy", "torch"],
        "code": "import numpy as np\nfrom PIL import Image\nimport cv2\nimport os\n\ndef load_davis_sequence(data_root, sequence_name):\n    \"\"\"Load a DAVIS sequence\"\"\"\n    images_path = os.path.join(\n        data_root, 'JPEGImages', '480p', sequence_name\n    )\n    annotations_path = os.path.join(\n        data_root, 'Annotations', '480p', sequence_name\n    )\n    \n    images = sorted(os.listdir(images_path))\n    annotations = sorted(os.listdir(annotations_path))\n    \n    frames = []\n    masks = []\n    \n    for img_name, ann_name in zip(images, annotations):\n        img = cv2.imread(os.path.join(images_path, img_name))\n        mask = np.array(Image.open(\n            os.path.join(annotations_path, ann_name)\n        ))\n        frames.append(img)\n        masks.append(mask)\n    \n    return frames, masks\n\n# Usage\nframes, masks = load_davis_sequence(\n    'path/to/DAVIS',\n    'bear'\n)\nprint(f'Loaded {len(frames)} frames')\n",
        "citation": """@inproceedings{Perazzi2016,
  title={A Benchmark Dataset and Evaluation Methodology for Video Object Segmentation},
  author={Perazzi, Federico and Pont-Tuset, Jordi and McWilliams, Brian and Van Gool, Luc and Gross, Markus and Sorkine-Hornung, Alexander},
  booktitle={CVPR},
  year={2016}
}""",
        "num_training_samples": 60,
        "num_validation_samples": 30,
        "num_classes": "DAVIS 2016: 1 object/video, DAVIS 2017: multiple objects",
        "image_size": "Full HD (1920x1080), 30fps",
        "release_year": 2016,
    },
    "Mapillary-Vistas": {
        "description": "A diverse street-level imagery dataset with pixel-accurate and instance-specific human annotations for understanding street scenes around the world. The dataset contains high-resolution images annotated into semantic object categories using polygons for delineating individual objects.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["semantic-segmentation"],
        "huggingface_url": "https://huggingface.co/datasets/candylion/mapillary-vistas-v2",
        "dependent_packages": ["datasets", "transformers", "PIL", "torch"],
        "code": """from datasets import load_dataset

# Load the dataset
dataset = load_dataset("candylion/mapillary-vistas-v2")

# Access training data
train_data = dataset['train']

# Load a sample
sample = train_data[0]
image = sample['image']
annotation = sample['annotation']""",
        "citation": """@inproceedings{Neuhold_ICCV_2017,
  author = {Gerhard Neuhold and Tobias Ollmann and Samuel Rota Bulò and Peter Kontschieder},
  title = {The Mapillary Vistas Dataset for Semantic Understanding of Street Scenes},
  booktitle = {International Conference on Computer Vision (ICCV)},
  year = {2017}
}""",
        "num_training_samples": 18000,
        "num_validation_samples": 7000,
        "num_classes": 124,
        "image_size": "variable (high-resolution)",
        "release_year": 2020,
    },
    "CIFAR-10": {
        "description": "CIFAR-10 is a dataset of 60,000 32x32 color images in 10 classes: airplane, automobile, bird, cat, deer, dog, frog, horse, ship, and truck. One of the most widely used fundamental benchmarks in deep learning research.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/uoft-cs/cifar10",
        "dependent_packages": ["datasets", "torch", "torchvision", "PIL"],
        "code": """from datasets import load_dataset
import matplotlib.pyplot as plt
import numpy as np

# Load CIFAR-10 dataset
dataset = load_dataset("uoft-cs/cifar10")

train_data = dataset['train']
test_data = dataset['test']

# Class names
class_names = [
    'airplane', 'automobile', 'bird', 'cat', 'deer',
    'dog', 'frog', 'horse', 'ship', 'truck'
]

# Visualize samples
fig, axes = plt.subplots(3, 3, figsize=(10, 10))
for i, ax in enumerate(axes.flat):
    idx = np.random.randint(len(train_data))
    sample = train_data[idx]
    ax.imshow(sample['img'])
    ax.set_title(class_names[sample['label']])
    ax.axis('off')
plt.tight_layout()
plt.show()

# PyTorch alternative
import torchvision
cifar10_train = torchvision.datasets.CIFAR10(
    root='./data',
    train=True,
    download=True
)
""",
        "citation": """@techreport{krizhevsky2009learning,
  title={Learning multiple layers of features from tiny images},
  author={Krizhevsky, Alex and Hinton, Geoffrey},
  institution={University of Toronto},
  year={2009}
}""",
        "num_training_samples": 50000,
        "num_validation_samples": 10000,
        "num_classes": 10,
        "image_size": "32x32 (RGB)",
        "release_year": 2009,
    },
    "GTSRB": {
        "description": "A multi-class classification dataset featuring 43 classes of traffic signs. The images were cropped from a larger set to focus on the traffic sign and eliminate background. Includes multiple augmented test sets to benchmark model robustness.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/tanganke/gtsrb",
        "dependent_packages": ["datasets", "PIL", "numpy", "torch"],
        "code": """from datasets import load_dataset

# Load GTSRB dataset
dataset = load_dataset('tanganke/gtsrb')

# Access different splits
train_data = dataset['train']
test_data = dataset['test']

# Access robustness test sets
contrast_test = dataset['contrast']
gaussian_noise_test = dataset['gaussian_noise']

# Example usage
sample = train_data[0]
image = sample['image']
label = sample['label']""",
        "citation": """@article{stallkampManVsComputer2012,
  title = {Man vs. Computer: Benchmarking Machine Learning Algorithms for Traffic Sign Recognition},
  author = {Stallkamp, J. and Schlipsing, M. and Salmen, J. and Igel, C.},
  year = {2012},
  journal = {Neural Networks},
  volume = {32},
  pages = {323--332}
}""",
        "num_training_samples": 26640,
        "num_validation_samples": 12630,
        "num_classes": 43,
        "image_size": "variable",
        "release_year": 2012,
    },
    "AQUA20": {
        "description": "A Benchmark Dataset for Underwater Species Classification in challenging conditions. Large-scale dataset with 8,171 samples across 20 different categories including fish, coral, marine plants, sharks, and shrimp. Contains visual constraints specific to underwater environments (color distortion, low contrast, variable lighting).",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/taufiktrf/AQUA20",
        "dependent_packages": ["datasets", "torch", "transformers", "PIL", "numpy"],
        "code": """from datasets import load_dataset
import matplotlib.pyplot as plt
import numpy as np
from transformers import AutoImageProcessor, AutoModelForImageClassification

# Load AQUA20 dataset
dataset = load_dataset("taufiktrf/AQUA20")

train_data = dataset['train']
val_data = dataset['validation']
test_data = dataset['test']

# 20 marine species categories
species_names = [
    'Clownfish', 'Coral', 'Crab', 'Dolphin', 'Eel',
    'Jellyfish', 'Lobster', 'Nudibranchs', 'Octopus', 'Penguin',
    'Pufferfish', 'Ray', 'Seahorse', 'Seal', 'Shark',
    'Shrimp', 'Squid', 'Starfish', 'Turtle', 'Whale'
]

# Visualize samples
fig, axes = plt.subplots(4, 5, figsize=(20, 16))
for i, ax in enumerate(axes.flat):
    idx = np.random.randint(len(train_data))
    sample = train_data[idx]
    ax.imshow(sample['image'])
    ax.set_title(species_names[sample['label']])
    ax.axis('off')
plt.tight_layout()
plt.show()
""",
        "citation": """@article{aqua20_2024,
  title={AQUA20: A Benchmark Dataset for Underwater Species Classification},
  author={Taufikurrahman and others},
  year={2024}
}""",
        "num_training_samples": 6537,
        "num_validation_samples": 817,
        "num_classes": 20,
        "image_size": "variable",
        "release_year": 2024,
    },
    "ImageNet-1K": {
        "description": "ImageNet ILSVRC 2012 is a large-scale image classification dataset with 1,000 classes from WordNet. It contains 1,281,167 training images, 50,000 validation images, and 100,000 test images. It is a standard benchmark in computer vision.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/ILSVRC/imagenet-1k",
        "dependent_packages": ["datasets", "torchvision", "PIL"],
        "code": """from datasets import load_dataset
# Load ImageNet dataset
dataset = load_dataset("ILSVRC/imagenet-1k")
train_data = dataset['train']
val_data = dataset['validation']
test_data = dataset['test']
image = train_data[0]['image']
label = train_data[0]['label']""",
        "citation": """@article{russakovsky2015imagenet,
  title={ImageNet Large Scale Visual Recognition Challenge},
  author={Russakovsky, Olga and Deng, Jia and Su, Hao and Krause, Jonathan and Satheesh, Sanjeev and Ma, Sean and Huang, Zhiheng and Karpathy, Andrej and Khosla, Aditya and Bernstein, Michael and Berg, Alexander C and Fei-Fei, Li},
  journal={International Journal of Computer Vision},
  volume={115},
  number={3},
  pages={211--252},
  year={2015}
}""",
        "num_training_samples": 1281167,
        "num_validation_samples": 50000,
        "num_classes": 1000,
        "image_size": "variable (typically resized to 224x224)",
        "release_year": 2012,
    },
    "CheXpert": {
        "description": "CheXpert is a large chest X-ray dataset of 224,316 images from 65,240 patients, labeled for 14 observations (e.g., pneumonia, edema) with uncertainty labels. It is used for evaluating radiographic diagnosis models.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/stanfordmlgroup/chexpert",
        "dependent_packages": ["datasets", "numpy", "pandas"],
        "code": """from datasets import load_dataset
# Load CheXpert dataset
dataset = load_dataset("stanfordmlgroup/chexpert")
image = dataset['train'][0]['image']
labels = dataset['train'][0]['labels']""",
        "citation": """@article{irvin2019chexpert,
  title={CheXpert: A Large Chest Radiograph Dataset with Uncertainty Labels and Expert Comparison},
  author={Irvin, Jeremy and Rajpurkar, Pranav and Ko, Eric and Yu, Yifan and Ciurea-Ilcus, Sebastian and Chute, Christopher and Marklund, Henrik and Ball, Robyn and Shpanskaya, Katie and Seekins, Joel and others},
  journal={Proceedings of the AAAI Conference on Artificial Intelligence},
  volume={33},
  number={01},
  pages={590--597},
  year={2019}
}""",
        "num_training_samples": 224316,
        "num_validation_samples": 0,
        "num_classes": 14,
        "image_size": "variable (e.g., 320x320)",
        "release_year": 2019,
    },
    "AFHQ": {
        "description": "Animal Faces-HQ (AFHQ) is a dataset of 15,000 high-quality animal face images (512x512) from 3 categories: cats, dogs, and wild animals (5000 each). Used for fine-grained classification and generative modeling.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/elozano/afhq",
        "dependent_packages": ["datasets", "PIL"],
        "code": """from datasets import load_dataset
# Load AFHQ dataset
dataset = load_dataset("elozano/afhq")
image = dataset['train'][0]['image']
label = dataset['train'][0]['label']""",
        "citation": """@inproceedings{choi2020stargan,
  title={StarGAN v2: Diverse Image Synthesis for Multiple Domains},
  author={Choi, Yunjey and Uh, Jeongtae and Yoo, Jongwook and Ha, Jung-Woo},
  booktitle={CVPR},
  pages={8188--8197},
  year={2020}
}""",
        "num_training_samples": 15000,
        "num_validation_samples": 0,
        "num_classes": 3,
        "image_size": "512x512 (RGB)",
        "release_year": 2020,
    },
    "ImageNet-A": {
        "description": "ImageNet-A: 7,500 natural adversarial examples (images) that fool ImageNet classifiers. Covers 200 classes.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/imagenet_a",
        "dependent_packages": ["datasets", "PIL"],
        "code": """from datasets import load_dataset
imagenet_a = load_dataset('imagenet_a', split='train')
image = imagenet_a[0]['image']
label = imagenet_a[0]['label']""",
        "citation": """@inproceedings{hendrycks2021natural,
  title={Natural Adversarial Examples},
  author={Hendrycks, Dan and Mu, Kevin and Cubuk, Ekin and Gilmer, Justin and Zhang, Balaji and Madry, Aleksander},
  booktitle={CVPR},
  pages={15262--15271},
  year={2021}
}""",
        "num_training_samples": 0,
        "num_validation_samples": 7500,
        "num_classes": 200,
        "image_size": "variable",
        "release_year": 2020,
    },
    "ImageNet-R": {
        "description": "ImageNet-R (Renditions): 30,000 images of stylized renditions of ImageNet classes (art, cartoons, etc) to test style robustness.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/imagenet_r",
        "dependent_packages": ["datasets", "PIL"],
        "code": """imagenet_r = load_dataset('imagenet_r', split='train')
image = imagenet_r[0]['image']""",
        "citation": """@inproceedings{hendrycks2021natural,
  title={Natural Adversarial Examples},
  author={Hendrycks, Dan and Mu, Kevin and Cubuk, Ekin and Gilmer, Justin and Zhang, Balaji and Madry, Aleksander},
  booktitle={CVPR},
  pages={15262--15271},
  year={2021}
}""",
        "num_training_samples": 0,
        "num_validation_samples": 30000,
        "num_classes": 200,
        "image_size": "variable",
        "release_year": 2020,
    },
    "CIFAR-10.1": {
        "description": "CIFAR-10.1: held-out test set of 2,000 images for CIFAR-10, used to measure model generalization.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/cifar10.1",
        "dependent_packages": ["datasets", "numpy"],
        "code": """from datasets import load_dataset
cifar101 = load_dataset('cifar10.1', split='test')
image = cifar101[0]['img']
label = cifar101[0]['label']""",
        "citation": """@inproceedings{recht2019imagenet,
  title={Do CIFAR-10 Classifiers Generalize to CIFAR-10?},
  author={Recht, Benjamin and Roelofs, Rebecca and Schmidt, Ludwig and Shankar, Vaishaal},
  booktitle={ICML},
  pages={5389--5400},
  year={2019}
}""",
        "num_training_samples": 0,
        "num_validation_samples": 2000,
        "num_classes": 10,
        "image_size": "32x32 (RGB)",
        "release_year": 2019,
    },
    "Beans": {
        "description": "A dataset of bean leaf images taken in the field using smartphone cameras in Uganda. Created to build machine learning models for distinguishing diseases in bean plants. Consists of 3 classes: healthy leaves and two disease classes (Angular Leaf Spot and Bean Rust).",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/AI-Lab-Makerere/beans",
        "dependent_packages": ["datasets", "PIL", "numpy", "torch"],
        "code": """from datasets import load_dataset

# Load Beans dataset
dataset = load_dataset("AI-Lab-Makerere/beans")

# Access splits
train_data = dataset['train']
validation_data = dataset['validation']
test_data = dataset['test']

# Example usage
sample = train_data[10]
image = sample['image']
label = sample['labels']""",
        "citation": """@ONLINE{beansdata,
  author = {Makerere AI Lab},
  title = {Bean disease dataset},
  month = {January},
  year = {2020},
  url = {https://github.com/AI-Lab-Makerere/ibean/}
}""",
        "num_training_samples": 1034,
        "num_validation_samples": 261,
        "num_classes": 3,
        "image_size": "500x500 (RGB)",
        "release_year": 2020,
    },
    "MIT-Indoor-Scenes": {
        "description": "Indoor scene recognition dataset with images from 67 different indoor categories. Images have been preprocessed with auto-orientation of pixel data and resized to uniform dimensions. The dataset covers various indoor environments like airports, bedrooms, churches, offices, etc.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/keremberke/indoor-scene-classification",
        "dependent_packages": ["datasets", "PIL", "Python"],
        "code": """from datasets import load_dataset

# Load the dataset
ds = load_dataset("keremberke/indoor-scene-classification", name="full")

# Access the first training example
example = ds['train'][0]
image = example['image']
label = example['label']""",
        "citation": """@inproceedings{quattoni2009recognizing,
  title={Recognizing indoor scenes},
  author={Quattoni, Ariadna and Torralba, Antonio},
  booktitle={2009 IEEE conference on computer vision and pattern recognition},
  pages={413--420},
  year={2009},
  organization={IEEE}
}""",
        "num_training_samples": 15571,
        "num_validation_samples": 0,
        "num_classes": 67,
        "image_size": "416x416",
        "release_year": 2009,
    },
    "Cats-vs-Dogs": {
        "description": "A large set of images of cats and dogs from the Asirra (Animal Species Image Recognition for Restricting Access) dataset. Contains 23,410 images after removing corrupted images. The dataset has enormous diversity in photo backgrounds, angles, poses, lighting.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-classification"],
        "huggingface_url": "https://huggingface.co/datasets/microsoft/cats_vs_dogs",
        "dependent_packages": ["datasets", "PIL", "Python"],
        "code": """from datasets import load_dataset

# Load the dataset
dataset = load_dataset("microsoft/cats_vs_dogs")

# Access a sample
example = dataset["train"][0]
image = example["image"]
label = example["labels"]

# Label mapping: 0 = cat, 1 = dog""",
        "citation": """@InProceedings{asirra-a-captcha-that-exploits-interest-aligned-manual-image-categorization,
  author = {Elson, Jeremy and Douceur, John (JD) and Howell, Jon and Saul, Jared},
  title = {Asirra: A CAPTCHA that Exploits Interest-Aligned Manual Image Categorization},
  booktitle = {Proceedings of 14th ACM Conference on Computer and Communications Security (CCS)},
  year = {2007},
  publisher = {Association for Computing Machinery, Inc.}
}""",
        "num_training_samples": 23410,
        "num_validation_samples": 0,
        "num_classes": 2,
        "image_size": "variable",
        "release_year": 2013,
    },
    "Satellite-Building-Segmentation": {
        "description": "A dataset for building instance segmentation from satellite/aerial imagery. The dataset includes images from various locations captured under different conditions, annotated in COCO format for building detection and segmentation.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["instance-segmentation"],
        "huggingface_url": "https://huggingface.co/datasets/keremberke/satellite-building-segmentation",
        "dependent_packages": ["datasets", "PIL", "numpy"],
        "code": """from datasets import load_dataset

# Load the dataset
ds = load_dataset("keremberke/satellite-building-segmentation", name="full")

# Access different splits
train_data = ds['train']
val_data = ds['validation']
test_data = ds['test']

# Load a sample
example = train_data[0]
image = example['image']
objects = example['objects']""",
        "citation": """@misc{buildings-instance-segmentation_dataset,
  title = {Buildings Instance Segmentation Dataset},
  type = {Open Source Dataset},
  author = {Roboflow Universe Projects},
  year = {2023},
  publisher = {Roboflow}
}""",
        "num_training_samples": 6764,
        "num_validation_samples": 2901,
        "num_classes": 1,
        "image_size": "500x500",
        "release_year": 2023,
    },
    "LoveDA": {
        "description": "A remote sensing land-cover dataset for domain adaptive semantic segmentation. The dataset contains high spatial resolution (0.3 m) remote sensing images from Nanjing, Changzhou, and Wuhan, encompassing two domains (urban and rural).",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["semantic-segmentation"],
        "huggingface_url": "https://huggingface.co/datasets/chloechia/loveda",
        "dependent_packages": ["datasets", "PIL", "numpy"],
        "code": """from datasets import load_dataset

# Load the dataset
dataset = load_dataset("chloechia/loveda")

# Access training data
train_data = dataset['train']

# Load a sample
sample = train_data[0]
image = sample['image']  # RGB image
label = sample['label']  # Segmentation mask""",
        "citation": """@inproceedings{NEURIPS_DATASETS_AND_BENCHMARKS2021_4e732ced,
  author = {Wang, Junjue and Zheng, Zhuo and Ma, Ailong and Lu, Xiaoyan and Zhong, Yanfei},
  title = {LoveDA: A Remote Sensing Land-Cover Dataset for Domain Adaptive Semantic Segmentation},
  booktitle = {NeurIPS Datasets and Benchmarks},
  year = {2021}
}""",
        "num_training_samples": 2522,
        "num_validation_samples": 3465,
        "num_classes": 7,
        "image_size": "1024x1024",
        "release_year": 2021,
    },
    "Teeth-Segmentation": {
        "description": "A medical imaging dataset for automatic semantic segmentation and measurement of total length of teeth in panoramic X-ray images. The dataset was created for dental diagnostic information for the management of dental disorders, diseases, and conditions.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["semantic-segmentation"],
        "huggingface_url": "https://huggingface.co/datasets/SerdarHelli/SegmentationOfTeethPanoramicXRayImages",
        "dependent_packages": ["datasets", "PIL", "pandas"],
        "code": """from datasets import load_dataset

# Load the dataset
dataset = load_dataset("SerdarHelli/SegmentationOfTeethPanoramicXRayImages")

# Access training data
train_data = dataset['train']

# Load a sample
sample = train_data[0]
xray_image = sample['image']
segmentation_mask = sample['label']""",
        "citation": """@article{helli10tooth,
  title={Tooth Instance Segmentation on Panoramic Dental Radiographs Using U-Nets and Morphological Processing},
  author={HELLI, Serdar and HAMAMCI, Andaç},
  journal={Düzce Üniversitesi Bilim ve Teknoloji Dergisi},
  volume={10},
  number={1},
  pages={39--50}
}""",
        "num_training_samples": 116,
        "num_validation_samples": 0,
        "num_classes": 2,
        "image_size": "variable",
        "release_year": 2022,
    },
    "SceneParse150": {
        "description": "Scene parsing benchmark providing a standard training and evaluation platform for scene parsing algorithms. The dataset contains scene-centric images exhaustively annotated with 150 semantic categories including both stuff classes (wall, sky, road) and discrete objects (car, person, table).",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["semantic-segmentation"],
        "huggingface_url": "https://huggingface.co/datasets/zhoubolei/scene_parse_150",
        "dependent_packages": ["datasets", "PIL", "numpy", "torch", "matplotlib"],
        "code": """from datasets import load_dataset
import numpy as np

# Load the dataset
dataset = load_dataset("zhoubolei/scene_parse_150", split="train")

# Access a sample
sample = dataset[10]
image = sample['image']
scene_category = sample['scene_category']
annotation_mask = np.array(sample['annotation'])""",
        "citation": """@inproceedings{zhou2017scene,
  title={Scene Parsing through ADE20K Dataset},
  author={Zhou, Bolei and Zhao, Hang and Puig, Xavier and Fidler, Sanja and Barriuso, Adela and Torralba, Antonio},
  booktitle={CVPR},
  year={2017}
}""",
        "num_training_samples": 20210,
        "num_validation_samples": 5352,
        "num_classes": 150,
        "image_size": "variable (min 512px)",
        "release_year": 2017,
    },
    "DocLayNet": {
        "description": "DocLayNet is a human-annotated document layout segmentation dataset containing 80,863 unique pages from 6 document categories. It provides page-by-page layout segmentation ground-truth using bounding-boxes for 11 distinct class labels from diverse and complex layouts.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["object-detection"],
        "huggingface_url": "https://huggingface.co/datasets/ds4sd/DocLayNet",
        "dependent_packages": ["datasets", "PIL", "Python", "pycocotools"],
        "code": """from datasets import load_dataset

# Load the dataset
dataset = load_dataset("ds4sd/DocLayNet")

# Access examples
example = dataset['train'][0]
print(example['image'])
print(example['annotations'])""",
        "citation": """@article{doclaynet2022,
  title = {DocLayNet: A Large Human-Annotated Dataset for Document-Layout Segmentation},
  author = {Pfitzmann, Birgit and Auer, Christoph and Dolfi, Michele and Nassar, Ahmed S and Staar, Peter W J},
  booktitle = {KDD},
  year = {2022}
}""",
        "num_training_samples": 64690,
        "num_validation_samples": 16173,
        "num_classes": 11,
        "image_size": "variable (high-resolution)",
        "release_year": 2022,
    },
    "Flickr8k": {
        "description": "An image captioning dataset featuring images from Flickr with corresponding text captions. Each image is paired with 5 different captions describing the scene. The dataset contains various everyday activities and scenes, suitable for image-to-text generation and vision-language tasks.",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": ["image-captioning"],
        "huggingface_url": "https://huggingface.co/datasets/ariG23498/flickr8k",
        "dependent_packages": ["datasets", "PIL", "transformers", "torch"],
        "code": """from datasets import load_dataset
import pandas as pd

# Load the dataset
dataset = load_dataset("ariG23498/flickr8k", split='train')

# Access image and caption
sample = dataset[0]
image = sample['image']
caption = sample['caption']

print(f"Caption: {caption}")
image.show()""",
        "citation": """@inproceedings{hodosh2013framing,
  title={Framing Image Description as a Ranking Task: Data, Models and Evaluation Metrics},
  author={Hodosh, Micah and Young, Peter and Hockenmaier, Julia},
  booktitle={JAIR},
  year={2013}
}""",
        "num_training_samples": 8000,
        "num_validation_samples": 0,
        "num_classes": 0,
        "image_size": "variable (164-500+ px)",
        "release_year": 2013,
    },
    "cifar100": {
        "description": "Dataset Card for CIFAR-100 Dataset Summary The CIFAR-100 dataset consists of 60000 32x32 colour images in 100 classes, with 600 images per class. There are 500 training images and 100 testing images per class. There are 50000 training images and 10000 test images. The 100 classes",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": "image-classification",
        "huggingface_url": "https://huggingface.co/datasets/uoft-cs/cifar100",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("uoft-cs/cifar100")""",
        "citation": "",
    },
    "food101": {
        "description": "Dataset Card for Food-101 Dataset Summary This dataset consists of 101 food categories, with 101'000 images. For each class, 250 manually reviewed test images are provided as well as 750 training images. On purpose, the training images were not cleaned, and thus still contain som",
        "domain": "vision",
        "category": "image_recognition",
        "task_type": "image-classification",
        "huggingface_url": "https://huggingface.co/datasets/ethz/food101",
        "dependent_packages": ["datasets"],
        "code": """from datasets import load_dataset
ds = load_dataset("ethz/food101")""",
        "citation": "",
    },
}
