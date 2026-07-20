# Vla (embodied_ai): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
VLA_LIBRARIES: dict[str, dict[str, str | None]] = {
    "lerobot": {
        "description": "End-to-end robot learning (policies, datasets, simulation)",
        "domain": "embodied_ai",
        "category": "vla",
        "official_docs": "https://huggingface.co/docs/lerobot",
        "github": "https://github.com/huggingface/lerobot",
        "llms_txt": "https://huggingface.co/docs/lerobot/llms.txt",
        "llms_full_txt": "https://huggingface.co/docs/lerobot/llms-full.txt",
    },
    "openvla": {
        "description": "Open-source vision-language-action model for robot control",
        "domain": "embodied_ai",
        "category": "vla",
        "official_docs": "https://github.com/openvla/openvla",
        "github": "https://github.com/openvla/openvla",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "openpi": {
        "description": "Open-source vision-language-action models (pi0) by Physical Intelligence",
        "domain": "embodied_ai",
        "category": "vla",
        "official_docs": "https://github.com/Physical-Intelligence/openpi",
        "github": "https://github.com/Physical-Intelligence/openpi",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
