# Bioinformatics (science): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
BIOINFORMATICS_LIBRARIES: dict[str, dict[str, str | None]] = {
    "esm": {
        "description": "Protein language models (ESM3, ESM C)",
        "domain": "science",
        "category": "bioinformatics",
        "official_docs": "https://github.com/evolutionaryscale/esm",
        "github": "https://github.com/Biohub/esm",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "biopython": {
        "description": "Tools for biological computation (sequences, structures, phylogenetics)",
        "domain": "science",
        "category": "bioinformatics",
        "official_docs": "https://biopython.org/wiki/Documentation",
        "github": "https://github.com/biopython/biopython",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "scanpy": {
        "description": "Single-cell gene expression analysis at scale",
        "domain": "science",
        "category": "bioinformatics",
        "official_docs": "https://scanpy.readthedocs.io/en/stable",
        "github": "https://github.com/scverse/scanpy",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "openfold": {
        "description": "Trainable PyTorch reproduction of AlphaFold2",
        "domain": "science",
        "category": "bioinformatics",
        "official_docs": "https://openfold.readthedocs.io/en/latest",
        "github": "https://github.com/aqlaboratory/openfold",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
