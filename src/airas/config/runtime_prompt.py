from typing import Literal

RuntimeKeyType = Literal["github_actions_gpu", "github_actions_cpu"]

runtime_prompt_dict = {
    "github_actions_gpu": """\
NVIDIA Tesla T4 · 16 GB VRAM""",
    "github_actions_cpu": """\
cpu 500 MB""",
}
