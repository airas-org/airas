# science / medical documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
MEDICAL_LIBRARIES: dict[str, dict[str, str | None]] = {
    "monai": {
        "description": "Deep learning framework for medical imaging",
        "domain": "science",
        "category": "medical",
        "official_docs": "https://monai.readthedocs.io/en/stable",
        "github": "https://github.com/Project-MONAI/MONAI",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "pydicom": {
        "description": "Read, modify, and write DICOM medical imaging files",
        "domain": "science",
        "category": "medical",
        "official_docs": "https://pydicom.github.io/pydicom/stable",
        "github": "https://github.com/pydicom/pydicom",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "nibabel": {
        "description": "Read and write neuroimaging file formats (NIfTI, etc.)",
        "domain": "science",
        "category": "medical",
        "official_docs": "https://nipy.org/nibabel",
        "github": "https://github.com/nipy/nibabel",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "mne": {
        "description": "EEG/MEG neurophysiological data analysis",
        "domain": "science",
        "category": "medical",
        "official_docs": "https://mne.tools/stable",
        "github": "https://github.com/mne-tools/mne-python",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
