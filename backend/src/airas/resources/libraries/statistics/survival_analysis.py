# statistics / survival_analysis documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
SURVIVAL_ANALYSIS_LIBRARIES: dict[str, dict[str, str | None]] = {
    "lifelines": {
        "description": "Survival analysis (Kaplan-Meier, Cox regression)",
        "domain": "statistics",
        "category": "survival_analysis",
        "official_docs": "https://lifelines.readthedocs.io/en/latest",
        "github": "https://github.com/CamDavidsonPilon/lifelines",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "scikit-survival": {
        "description": "Survival analysis built on scikit-learn (random survival forests)",
        "domain": "statistics",
        "category": "survival_analysis",
        "official_docs": "https://scikit-survival.readthedocs.io/en/stable",
        "github": "https://github.com/sebp/scikit-survival",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
