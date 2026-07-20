# Bayesian Inference libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
BAYESIAN_INFERENCE_LIBRARIES: dict[str, dict[str, str | None]] = {
    "pymc": {
        "description": "Bayesian modeling with MCMC and variational inference",
        "category": "bayesian_inference",
        "official_docs": "https://www.pymc.io",
        "github": "https://github.com/pymc-devs/pymc",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "numpyro": {
        "description": "JAX-backed probabilistic programming (NUTS at scale)",
        "category": "bayesian_inference",
        "official_docs": "https://num.pyro.ai",
        "github": "https://github.com/pyro-ppl/numpyro",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
