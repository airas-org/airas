from typing import Literal

RunnerType = Literal["ubuntu-latest", "Tesla_T4", "A100_80GM×8"]

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
    "A100_80GM×8": {
        "runner_setting": '["self-hosted", "A100 80GM×8"]',
        "prompt": """\
NVIDIA A100×8
VRAM：80GB×8
RAM：2048 GB""",
    },
}
