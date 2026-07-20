# Mathematical Optimization libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
MATHEMATICAL_OPTIMIZATION_LIBRARIES: dict[str, dict[str, str | None]] = {
    "cvxpy": {
        "description": "Modeling language for convex optimization",
        "category": "mathematical_optimization",
        "official_docs": "https://www.cvxpy.org",
        "github": "https://github.com/cvxpy/cvxpy",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "pyomo": {
        "description": "Algebraic modeling for LP/MIP/NLP with solver interfaces",
        "category": "mathematical_optimization",
        "official_docs": "https://pyomo.readthedocs.io/en/stable",
        "github": "https://github.com/Pyomo/pyomo",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "ortools": {
        "description": "Google's combinatorial optimization (CP-SAT, routing, LP)",
        "category": "mathematical_optimization",
        "official_docs": "https://developers.google.com/optimization",
        "github": "https://github.com/google/or-tools",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
