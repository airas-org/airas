# Scientific Ml libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
SCIENTIFIC_ML_LIBRARIES: dict[str, dict[str, str | None]] = {
    "monai": {
        "description": "Deep learning framework for medical imaging",
        "category": "scientific_ml",
        "official_docs": "https://monai.readthedocs.io/en/stable",
        "github": "https://github.com/Project-MONAI/MONAI",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "rdkit": {
        "description": "Cheminformatics toolkit (molecules, descriptors, reactions)",
        "category": "scientific_ml",
        "official_docs": "https://www.rdkit.org/docs",
        "github": "https://github.com/rdkit/rdkit",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "deepchem": {
        "description": "ML for drug discovery, chemistry, and materials",
        "category": "scientific_ml",
        "official_docs": "https://deepchem.readthedocs.io/en/latest",
        "github": "https://github.com/deepchem/deepchem",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "physicsnemo": {
        "description": "Physics-ML framework (neural operators, PINNs)",
        "category": "scientific_ml",
        "official_docs": "https://docs.nvidia.com/physicsnemo/latest/index.html",
        "github": "https://github.com/NVIDIA/physicsnemo",
        "llms_txt": "https://docs.nvidia.com/llms.txt",
        "llms_full_txt": None,
    },
    "esm": {
        "description": "Protein language models (ESM3, ESM C)",
        "category": "scientific_ml",
        "official_docs": "https://github.com/evolutionaryscale/esm",
        "github": "https://github.com/Biohub/esm",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
