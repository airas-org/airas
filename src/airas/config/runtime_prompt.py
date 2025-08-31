from typing import Literal

RuntimeKeyType = Literal["gpu-runner", "default"]

runtime_prompt_dict = {
    "gpu-runner": """\
NVIDIA Tesla T4 · 16 GB VRAM""",
    "default": """\
cpu 500 MB""",
}
