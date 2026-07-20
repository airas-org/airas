# Statistics libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
STATISTICS_LIBRARIES: dict[str, dict[str, str | None]] = {
    "scipy": {
        "description": "Scientific computing (optimization, stats, signal processing)",
        "category": "statistics",
        "official_docs": "https://docs.scipy.org/doc/scipy",
        "github": "https://github.com/scipy/scipy",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "statsmodels": {
        "description": "Statistical models and hypothesis tests (regression, GLM, ANOVA)",
        "category": "statistics",
        "official_docs": "https://www.statsmodels.org/stable",
        "github": "https://github.com/statsmodels/statsmodels",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "pingouin": {
        "description": "Statistical tests on pandas data (ANOVA, t-tests, effect sizes)",
        "category": "statistics",
        "official_docs": "https://pingouin-stats.org",
        "github": "https://github.com/raphaelvallat/pingouin",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "lifelines": {
        "description": "Survival analysis (Kaplan-Meier, Cox regression)",
        "category": "statistics",
        "official_docs": "https://lifelines.readthedocs.io/en/latest",
        "github": "https://github.com/CamDavidsonPilon/lifelines",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
