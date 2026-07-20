from typing import TypeVar

from pydantic import BaseModel

from airas.infra.llm_specs import (
    LLMParams,
)


class NodeLLMConfig(BaseModel):
    # Use str instead of LLM_MODEL to allow model names compatible with
    # litellm and opencode rather than our custom defined literals.
    llm_name: str
    params: LLMParams | None = None


_MappingT = TypeVar("_MappingT", bound=BaseModel)


def require_llm_mapping(llm_mapping: _MappingT | None) -> _MappingT:
    """Return ``llm_mapping``, or raise a uniform error when it is ``None``.

    Every subgraph requires its model selection to be supplied externally
    (there are no in-code defaults). Centralizing the guard here keeps the
    message identical across all subgraphs and gives a single place to
    evolve the wording or add hints.
    """
    if llm_mapping is None:
        raise ValueError(
            "llm_mapping is required: specify the model(s) explicitly "
            "(no default model is configured)."
        )
    return llm_mapping


def uniform_llm_mapping(
    mapping_cls: type[_MappingT],
    model: str,
    params: LLMParams | None = None,
) -> _MappingT:
    """Build a subgraph LLM mapping whose every node uses the same model.

    There are intentionally no in-code per-node model defaults: model
    selection is supplied externally (MCP tool arguments, dashboard API
    requests, autonomous-research entry points). This helper lets a caller
    turn a single externally-chosen model name into the per-node mapping a
    subgraph requires, without having to name each node field explicitly.
    """
    # Build a fresh NodeLLMConfig per field — and a deep copy of params per
    # field — so nodes never share a mutable instance (mutating one node's
    # config or params must not affect the others).
    return mapping_cls(
        **{
            name: NodeLLMConfig(
                llm_name=model,
                params=params.model_copy(deep=True) if params is not None else None,
            )
            for name in mapping_cls.model_fields
        }
    )
