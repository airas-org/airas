# Jax Ecosystem (foundations): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
JAX_ECOSYSTEM_LIBRARIES: dict[str, dict[str, str | None]] = {
    "jax": {
        "description": "Composable transformations (grad, jit, vmap) with XLA",
        "domain": "foundations",
        "category": "jax_ecosystem",
        "official_docs": "https://docs.jax.dev",
        "github": "https://github.com/jax-ml/jax",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "flax": {
        "description": "Neural network library for JAX (NNX/Linen)",
        "domain": "foundations",
        "category": "jax_ecosystem",
        "official_docs": "https://flax.readthedocs.io/en/latest",
        "github": "https://github.com/google/flax",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "optax": {
        "description": "Gradient transformation and optimizer library for JAX",
        "domain": "foundations",
        "category": "jax_ecosystem",
        "official_docs": "https://optax.readthedocs.io/en/latest",
        "github": "https://github.com/google-deepmind/optax",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "equinox": {
        "description": "PyTorch-like neural networks as JAX PyTrees",
        "domain": "foundations",
        "category": "jax_ecosystem",
        "official_docs": "https://docs.kidger.site/equinox",
        "github": "https://github.com/patrick-kidger/equinox",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
