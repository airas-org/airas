# Audio (perception): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
AUDIO_LIBRARIES: dict[str, dict[str, str | None]] = {
    "whisper": {
        "description": "Robust speech recognition model and inference code",
        "domain": "perception",
        "category": "audio",
        "official_docs": "https://github.com/openai/whisper",
        "github": "https://github.com/openai/whisper",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "faster-whisper": {
        "description": "CTranslate2-accelerated Whisper inference",
        "domain": "perception",
        "category": "audio",
        "official_docs": "https://github.com/SYSTRAN/faster-whisper",
        "github": "https://github.com/SYSTRAN/faster-whisper",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "torchaudio": {
        "description": "Audio I/O, transforms, and models for PyTorch",
        "domain": "perception",
        "category": "audio",
        "official_docs": "https://docs.pytorch.org/audio/stable",
        "github": "https://github.com/pytorch/audio",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "espnet": {
        "description": "End-to-end speech processing toolkit (ASR, TTS, translation)",
        "domain": "perception",
        "category": "audio",
        "official_docs": "https://espnet.github.io/espnet",
        "github": "https://github.com/espnet/espnet",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "speechbrain": {
        "description": "PyTorch conversational AI toolkit (ASR, speaker, enhancement)",
        "domain": "perception",
        "category": "audio",
        "official_docs": "https://speechbrain.readthedocs.io/en/latest",
        "github": "https://github.com/speechbrain/speechbrain",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
