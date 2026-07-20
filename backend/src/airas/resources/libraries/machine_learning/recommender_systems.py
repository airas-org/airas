# machine_learning / recommender_systems documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
RECOMMENDER_SYSTEMS_LIBRARIES: dict[str, dict[str, str | None]] = {
    "implicit": {
        "description": "Fast collaborative filtering for implicit feedback datasets",
        "domain": "machine_learning",
        "category": "recommender_systems",
        "official_docs": "https://benfred.github.io/implicit",
        "github": "https://github.com/benfred/implicit",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "recbole": {
        "description": "Unified recommendation system framework (100+ algorithms)",
        "domain": "machine_learning",
        "category": "recommender_systems",
        "official_docs": "https://recbole.io",
        "github": "https://github.com/RUCAIBox/RecBole",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
