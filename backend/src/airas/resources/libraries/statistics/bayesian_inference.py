# statistics / bayesian_inference documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
BAYESIAN_INFERENCE_LIBRARIES: dict[str, dict[str, str | None]] = {
    "pymc": {
        "description": "Bayesian modeling with MCMC and variational inference",
        "domain": "statistics",
        "category": "bayesian_inference",
        "official_docs": "https://www.pymc.io",
        "github": "https://github.com/pymc-devs/pymc",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "numpyro": {
        "description": "JAX-backed probabilistic programming (NUTS at scale)",
        "domain": "statistics",
        "category": "bayesian_inference",
        "official_docs": "https://num.pyro.ai",
        "github": "https://github.com/pyro-ppl/numpyro",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "arviz": {
        "description": "Exploratory analysis of Bayesian models (diagnostics, plots)",
        "domain": "statistics",
        "category": "bayesian_inference",
        "official_docs": "https://python.arviz.org/en/stable",
        "github": "https://github.com/arviz-devs/arviz",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "cmdstanpy": {
        "description": "Python interface to the Stan probabilistic programming language",
        "domain": "statistics",
        "category": "bayesian_inference",
        "official_docs": "https://mc-stan.org/cmdstanpy",
        "github": "https://github.com/stan-dev/cmdstanpy",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
