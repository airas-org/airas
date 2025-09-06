from typing import Literal

RunnerTypeKey = Literal[
    "ubuntu-latest", "gpu-runner", "pt80-1-a-25", "t-80-8-b-01", "t-80-8-b-03"
]

runner_type_prompt_dict = {
    "ubuntu-latest": """\
cpu
RAM：500 MB""",
    "gpu-runner": """\
NVIDIA Tesla T4
VRAM：16 GB
RAM：500 MB""",
    "pt80-1-a-25": """\
NVIDIA A100×1
VRAM：80GB×1
RAM：256GB""",
    "t-80-8-b-01": """\
NVIDIA A100×8
VRAM：80GB×8
RAM：2048 GB""",
    "t-80-8-b-03": """\
NVIDIA A100×8
VRAM：80GB×8
RAM：2048 GB""",
}
