# Decision Making (decision_science): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
DECISION_MAKING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "obp": {
        "description": "Off-policy evaluation and bandit algorithms (Open Bandit Pipeline)",
        "domain": "decision_science",
        "category": "decision_making",
        "official_docs": "https://zr-obp.readthedocs.io/en/latest",
        "github": "https://github.com/st-tech/zr-obp",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "pymdp": {
        "description": "Active inference and POMDP agents",
        "domain": "decision_science",
        "category": "decision_making",
        "official_docs": "https://pymdp-rtd.readthedocs.io/en/latest",
        "github": "https://github.com/infer-actively/pymdp",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
