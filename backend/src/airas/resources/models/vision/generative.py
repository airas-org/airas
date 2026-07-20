# Curated model registry (see resources/models/registry.py for the
# subfield aggregation). HuggingFace URLs and arXiv citations are verified
# on entry; add candidates via search_huggingface_hub for un-curated needs.
IMAGE_GENERATIVE_MODELS: dict = {
    "sdxl-base-1.0": {
        "model_parameters": "2.6B",
        "model_architecture": "Diffusion-based image generation model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0",
        "task_type": "text-to-image",
        "dependent_packages": ["diffusers", "torch"],
        "code": """from diffusers import DiffusionPipeline
pipe = DiffusionPipeline.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0")
image = pipe("a photo of an astronaut riding a horse").images[0]""",
        "citation": """@misc{podell2023,
  title = {SDXL: Improving Latent Diffusion Models for High-Resolution Image Synthesis},
  author = {Dustin Podell and Zion English and Kyle Lacey and Andreas Blattmann and Tim Dockhorn and Jonas Müller and Joe Penna and Robin Rombach},
  year = {2023},
  eprint = {2307.01952},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2307.01952}
}""",
    },
    "ddpm-cifar10": {
        "model_parameters": "36M",
        "model_architecture": "Diffusion-based image generation model.",
        "training_data_sources": "",
        "huggingface_url": "https://huggingface.co/google/ddpm-cifar10-32",
        "task_type": "unconditional-image-generation",
        "dependent_packages": ["diffusers", "torch"],
        "code": """from diffusers import DDPMPipeline
pipe = DDPMPipeline.from_pretrained("google/ddpm-cifar10-32")
image = pipe().images[0]""",
        "citation": """@misc{ho2020,
  title = {Denoising Diffusion Probabilistic Models},
  author = {Jonathan Ho and Ajay Jain and Pieter Abbeel},
  year = {2020},
  eprint = {2006.11239},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2006.11239}
}""",
    },
}
