# Vision libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
VISION_LIBRARIES: dict[str, dict[str, str | None]] = {
    "timm": {
        "description": "PyTorch image models (backbones, augmentations, training recipes)",
        "category": "vision",
        "official_docs": "https://huggingface.co/docs/timm",
        "github": "https://github.com/huggingface/pytorch-image-models",
        "llms_txt": "https://huggingface.co/docs/timm/llms.txt",
        "llms_full_txt": "https://huggingface.co/docs/timm/llms-full.txt",
    },
    "torchvision": {
        "description": "Vision datasets, transforms, and pretrained models for PyTorch",
        "category": "vision",
        "official_docs": "https://docs.pytorch.org/vision/stable",
        "github": "https://github.com/pytorch/vision",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "diffusers": {
        "description": "Diffusion model pipelines, schedulers, and training",
        "category": "vision",
        "official_docs": "https://huggingface.co/docs/diffusers",
        "github": "https://github.com/huggingface/diffusers",
        "llms_txt": "https://huggingface.co/docs/diffusers/llms.txt",
        "llms_full_txt": "https://huggingface.co/docs/diffusers/llms-full.txt",
    },
    "open-clip": {
        "description": "Open-source CLIP training and pretrained checkpoints",
        "category": "vision",
        "official_docs": "https://github.com/mlfoundations/open_clip",
        "github": "https://github.com/mlfoundations/open_clip",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "ultralytics": {
        "description": "YOLO family detection and segmentation training/deployment",
        "category": "vision",
        "official_docs": "https://docs.ultralytics.com",
        "github": "https://github.com/ultralytics/ultralytics",
        "llms_txt": "https://docs.ultralytics.com/llms.txt",
        "llms_full_txt": None,
    },
    "sam2": {
        "description": "Promptable image and video segmentation (Segment Anything 2)",
        "category": "vision",
        "official_docs": "https://github.com/facebookresearch/sam2",
        "github": "https://github.com/facebookresearch/sam2",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "kornia": {
        "description": "Differentiable computer vision operators for PyTorch",
        "category": "vision",
        "official_docs": "https://kornia.readthedocs.io/en/latest",
        "github": "https://github.com/kornia/kornia",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
