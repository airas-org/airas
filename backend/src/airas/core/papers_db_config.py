# Base URL for the airas-papers-db repository (GitHub raw content)
AIRAS_PAPERS_REPO_BASE_URL = (
    "https://raw.githubusercontent.com/airas-org/airas-papers-db/main/data"
)

# Conferences and years to include in the database
# NOTE: Only uncommented conferences are actively used
CONFERENCES_AND_YEARS = {
    # ==================== Core Machine Learning (ML) ====================
    "iclr": ["2020", "2021", "2022", "2023", "2024", "2025"],
    "icml": ["2020", "2021", "2022", "2023", "2024", "2025"],
    "neurips": ["2020", "2021", "2022", "2023", "2024", "2025"],
    # ==================== Natural Language Processing (NLP) ====================
    "acl": ["2020", "2021", "2022", "2023", "2024"],
    "emnlp": ["2020", "2021", "2022", "2023", "2024"],
    "naacl": ["2021", "2022", "2024"],
    # ==================== Computer Vision (CV) ====================
    # "cvpr": ["2023", "2024", "2025"],
    # "eccv": ["2024"],
    # ==================== ML Theory ====================
    # "colt": ["2019", "2020", "2021", "2022", "2023", "2024", "2025"],
    # "aabi": ["2018", "2019", "2024", "2025"],
    # ==================== Statistical / Probabilistic ML ====================
    # "aistats": ["2019", "2020", "2021", "2022", "2023", "2024", "2025"],
    # "uai":     ["2019", "2020", "2021", "2022", "2023", "2024", "2025"],
    # "pgm":     ["2016", "2020", "2022", "2024"],
}
