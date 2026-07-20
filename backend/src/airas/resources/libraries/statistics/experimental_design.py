# Experimental Design (statistics): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
EXPERIMENTAL_DESIGN_LIBRARIES: dict[str, dict[str, str | None]] = {
    "ax": {
        "description": "Adaptive experimentation platform for A/B tests and Bayesian optimization",
        "domain": "statistics",
        "category": "experimental_design",
        "official_docs": "https://ax.dev",
        "github": "https://github.com/facebook/Ax",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "botorch": {
        "description": "Bayesian optimization library built on PyTorch",
        "domain": "statistics",
        "category": "experimental_design",
        "official_docs": "https://botorch.org",
        "github": "https://github.com/meta-pytorch/botorch",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "pydoe3": {
        "description": "Design of experiments generation (factorial, response surface)",
        "domain": "statistics",
        "category": "experimental_design",
        "official_docs": "https://pydoe3.readthedocs.io/en/stable",
        "github": "https://github.com/relf/pyDOE3",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
