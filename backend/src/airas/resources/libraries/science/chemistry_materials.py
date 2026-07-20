# science / chemistry_materials documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
CHEMISTRY_MATERIALS_LIBRARIES: dict[str, dict[str, str | None]] = {
    "rdkit": {
        "description": "Cheminformatics toolkit (molecules, descriptors, reactions)",
        "domain": "science",
        "category": "chemistry_materials",
        "official_docs": "https://www.rdkit.org/docs",
        "github": "https://github.com/rdkit/rdkit",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "deepchem": {
        "description": "ML for drug discovery, chemistry, and materials",
        "domain": "science",
        "category": "chemistry_materials",
        "official_docs": "https://deepchem.readthedocs.io/en/latest",
        "github": "https://github.com/deepchem/deepchem",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "ase": {
        "description": "Atomic Simulation Environment for atomistic calculations",
        "domain": "science",
        "category": "chemistry_materials",
        "official_docs": "https://wiki.fysik.dtu.dk/ase",
        "github": "https://gitlab.com/ase/ase",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "pymatgen": {
        "description": "Materials analysis (structures, phase diagrams, Materials Project)",
        "domain": "science",
        "category": "chemistry_materials",
        "official_docs": "https://pymatgen.org",
        "github": "https://github.com/materialsproject/pymatgen",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "openmm": {
        "description": "GPU-accelerated molecular dynamics simulation",
        "domain": "science",
        "category": "chemistry_materials",
        "official_docs": "https://docs.openmm.org/latest/userguide",
        "github": "https://github.com/openmm/openmm",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
