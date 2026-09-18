import logging
from typing import Any

from airas.core.llm_config import NodeLLMConfig
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.infra.litellm_client import LiteLLMClient
from airas.usecases.reproduction.nodes.fetch_reproduction_outputs import (
    fetch_reproduction_outputs,
)
from airas.usecases.reproduction.nodes.judge_reproduction import judge_reproduction
from airas.usecases.reproduction.nodes.parameter_check import (
    cross_check_parameters,
)
from airas.usecases.reproduction.nodes.parameter_check import (
    format_evidence as format_parameter_evidence,
)
from airas.usecases.reproduction.nodes.parse_reproduction_config import (
    parse_reproduction_config,
)
from airas.usecases.reproduction.nodes.pitfall_check import (
    format_evidence as format_pitfall_evidence,
)
from airas.usecases.reproduction.nodes.pitfall_check import (
    run_pitfall_checklist,
)
from airas.usecases.reproduction.nodes.validate_repro_id import validate_repro_id

logger = logging.getLogger(__name__)

_EMPTY: dict[str, Any] = {
    "result": None,
    "validation": None,
    "parameter_check": None,
    "repro_md": None,
    "repro_png_base64": None,
}


async def fetch_paper_reproduction_results(
    github_client: GithubClient,
    litellm_client: LiteLLMClient,
    github_config: GitHubConfig,
    repro_id: str,
    llm_config: NodeLLMConfig,
) -> dict[str, Any]:
    """The run's self-reported result plus the backend's verdict on it:
    deterministic pitfall and parameter checks, then an LLM judge."""
    validate_repro_id(repro_id)
    try:
        outputs = await fetch_reproduction_outputs(
            github_client=github_client, github_config=github_config, repro_id=repro_id
        )
    except Exception as exc:
        logger.exception("Failed to fetch reproduction outputs")
        return {**_EMPTY, "final_status": {"status": "failed", "fetch_error": str(exc)}}

    public = {
        "result": outputs.get("result"),
        "repro_md": outputs.get("repro_md"),
        "repro_png_base64": outputs.get("repro_png_base64"),
    }
    result = public["result"]
    if not isinstance(result, dict):
        return {
            **_EMPTY,
            **public,
            "final_status": {"status": "failed", "run_error": "result_missing"},
        }
    if result.get("error"):
        # Early exit (target_not_found/gpu_required): nothing to validate.
        return {
            **_EMPTY,
            **public,
            "final_status": {"status": "failed", "run_error": result["error"]},
        }

    checklist = run_pitfall_checklist(
        reproduce_code=outputs.get("main_py"),
        run_log=outputs.get("run_log"),
        summary=str(result.get("summary", "")),
        repro_md=public["repro_md"],
        repro_png_base64=public["repro_png_base64"],
    )
    paper_extraction = outputs.get("paper_extraction")
    if not isinstance(paper_extraction, dict):  # agent-authored, not schema-validated
        paper_extraction = {}
    param_check = cross_check_parameters(
        reported_params=parse_reproduction_config(outputs.get("reproduction_yaml")),
        paper_params=paper_extraction.get("parameters") or [],
    )
    evidence = "\n\n".join(
        (format_pitfall_evidence(checklist), format_parameter_evidence(param_check))
    )
    try:
        validation = await judge_reproduction(
            llm_config=llm_config,
            litellm_client=litellm_client,
            paper_text=outputs.get("paper_txt"),
            result=result,
            evidence=evidence,
        )
    except Exception as exc:
        logger.exception("judge_reproduction failed")
        return {
            **public,
            "validation": None,
            "parameter_check": param_check,
            "final_status": {"status": "failed", "validation_error": str(exc)},
        }
    severity = validation.get("severity")
    # "warning" is treated as passed; only "critical" fails.
    return {
        **public,
        "validation": validation,
        "parameter_check": param_check,
        "final_status": {
            "status": "failed" if severity == "critical" else "passed",
            "validation_severity": severity,
            "reproduction_level": validation.get("reproduction_level"),
        },
    }
