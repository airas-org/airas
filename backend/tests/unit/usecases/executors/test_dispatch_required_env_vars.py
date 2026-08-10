"""An experiment that does not use W&B must be able to say so.

`required_env_vars` defaults to `["WANDB_API_KEY"]` and Seyval refuses to
start a run whose declared vars are not registered. The subgraph took the
argument but the MCP tool did not expose it, so there was no way to
override it — the only way through was to register a dummy key for an
experiment that never calls wandb.

The distinction that matters is `[]` versus `None`: "nothing is required"
has to be expressible, and must not collapse into "unspecified".
"""

import pytest

from airas.usecases.executors.dispatch_experiment_on_seyval_subgraph.dispatch_experiment_on_seyval_subgraph import (
    DispatchExperimentOnSeyvalSubgraph,
)


def _subgraph(**kwargs) -> DispatchExperimentOnSeyvalSubgraph:
    return DispatchExperimentOnSeyvalSubgraph(seyval_client=object(), **kwargs)


@pytest.mark.parametrize(
    ("supplied", "expected"),
    [
        (None, ["WANDB_API_KEY"]),
        ([], []),
        (["HF_TOKEN"], ["HF_TOKEN"]),
    ],
)
def test_an_empty_list_is_not_the_same_as_unspecified(supplied, expected):
    assert _subgraph(required_env_vars=supplied).required_env_vars == expected


def test_the_default_is_applied_when_the_argument_is_omitted():
    assert _subgraph().required_env_vars == ["WANDB_API_KEY"]
