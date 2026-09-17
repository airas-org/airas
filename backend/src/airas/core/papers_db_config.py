# Base URL for the airas-papers-db repository (GitHub raw content)
AIRAS_PAPERS_REPO_BASE_URL = (
    "https://raw.githubusercontent.com/airas-org/airas-papers-db/main/data"
)

# The store of research records AIRAS itself produced, collected from
# repositories whose gate passed (manifest.json + records/<owner>/<repo>/<sha>/).
AIRAS_RECORDS_REPO_BASE_URL = (
    "https://raw.githubusercontent.com/airas-org/airas-records-db/main"
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
    # ==================== Formal Methods / Theorem Proving ====================
    # The human-authored formalization and verification venues (Lean, Isabelle,
    # Rocq/Coq, automated deduction, model checking, logic, PL), for theory
    # claims verified in Lean. ITP 2020 was merged into IJCAR 2020; CADE runs
    # in odd years and IJCAR in even years.
    "itp": ["2019", "2021", "2022", "2023", "2024", "2025", "2026"],
    "cpp": ["2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"],
    "cade": ["2019", "2021", "2023", "2025"],
    "ijcar": ["2020", "2022", "2024", "2026"],
    "cav": ["2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"],
    "tacas": ["2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"],
    "lics": ["2019", "2020", "2021", "2022", "2023", "2024", "2025"],
    "popl": ["2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"],
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
    # ==================== Life Science ====================
    # "ml4lms": ["2024"],
    # "gem":    ["2024", "2025", "2026"],
    # "lmrl":   ["2022", "2025", "2026"],
    # "genbio": ["2023", "2025", "2026"],
    # "mlcb":   ["2021", "2022", "2023", "2024", "2025"],
}
