from typing import Literal

RunnerType = Literal[
    "ubuntu-latest",
    "Tesla_T4",
    "A100_80GM×1",
    "A100_80GM×8",
    "H200_144GM×8",
    "gpu-runner",
]

runner_info_dict = {
    "ubuntu-latest": {
        "runner_setting": '["ubuntu-latest"]',
        "prompt": """\
cpu
RAM：500 MB""",
    },
    "Tesla_T4": {
        "runner_setting": '["gpu-runner"]',
        "prompt": """\
NVIDIA Tesla T4
VRAM：16 GB
RAM：500 MB""",
    },
    "A100_80GM×1": {
        "runner_setting": '["self-hosted", "A100 80GM×1"]',
        "prompt": """\
NVIDIA A100
VRAM：80GB
RAM：2048 GB""",
    },
    "A100_80GM×8": {
        "runner_setting": '["self-hosted", "A100 80GM×8"]',
        "prompt": """\
NVIDIA A100×8
VRAM：80GB×8
RAM：2048 GB""",
    },
    "H200_144GM×8": {
        "runner_setting": '["self-hosted", "H200 144GM×8"]',
        "prompt": """\
NVIDIA H200×8
VRAM: 144GB×8
RAM： 2048 GB or more""",
    },
    "gpu-runner": {
        "runner_setting": '["self-hosted", "gpu-runner"]',
        "prompt": """\
NVIDIA A100 or H200
VRAM: 80 GB or more
RAM: 2048 GB or more""",
    },
}
