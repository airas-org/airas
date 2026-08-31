# statistics / statistical_analysis documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
STATISTICAL_ANALYSIS_LIBRARIES: dict[str, dict[str, str | None]] = {
    "scipy": {
        "description": "Scientific computing (optimization, stats, signal processing)",
        "domain": "statistics",
        "category": "statistical_analysis",
        "official_docs": "https://docs.scipy.org/doc/scipy",
        "github": "https://github.com/scipy/scipy",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "statsmodels": {
        "description": "Statistical models and hypothesis tests (regression, GLM, ANOVA)",
        "domain": "statistics",
        "category": "statistical_analysis",
        "official_docs": "https://www.statsmodels.org/stable",
        "github": "https://github.com/statsmodels/statsmodels",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "pingouin": {
        "description": "Statistical tests on pandas data (ANOVA, t-tests, effect sizes)",
        "domain": "statistics",
        "category": "statistical_analysis",
        "official_docs": "https://pingouin-stats.org",
        "github": "https://github.com/raphaelvallat/pingouin",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
