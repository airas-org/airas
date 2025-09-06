from typing import Literal

RunnerTypeKey = Literal["ubuntu-latest", "gpu-runner"]

runner_type_prompt_dict = {
    "ubuntu-latest": "cpu 500 MB",
    "gpu-runner": "NVIDIA Tesla T4 · 16 GB VRAM",
}
