import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLM_CONFIG, NodeLLMConfig
from airas.core.logging_utils import setup_logging
from airas.infra.litellm_client import LiteLLMClient

setup_logging()
logger = logging.getLogger(__name__)


def record_execution_time(f):
    return time_node("generate_verification_method_subgraph")(f)  # noqa: E731


class ExperimentSetting(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str
    description: str


class VerificationMethodOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    what_to_verify: str
    experiment_settings: list[ExperimentSetting]
    steps: list[str]


class GenerateVerificationMethodLLMMapping(BaseModel):
    generate_verification_method: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "generate_verification_method"
    ]


class GenerateVerificationMethodSubgraphInputState(TypedDict):
    user_query: str
    selected_policy_title: str
    selected_policy_what_to_verify: str
    selected_policy_method: str


class GenerateVerificationMethodSubgraphOutputState(ExecutionTimeState):
    what_to_verify: str
    experiment_settings: dict[str, str]
    steps: list[str]


class GenerateVerificationMethodSubgraphState(
    GenerateVerificationMethodSubgraphInputState,
    GenerateVerificationMethodSubgraphOutputState,
    total=False,
):
    pass


class GenerateVerificationMethodSubgraph:
    def __init__(
        self,
        litellm_client: LiteLLMClient,
        llm_mapping: GenerateVerificationMethodLLMMapping | None = None,
    ):
        self.litellm_client = litellm_client
        self.llm_mapping = llm_mapping or GenerateVerificationMethodLLMMapping()

    @record_execution_time
    async def _generate_verification_method(
        self, state: GenerateVerificationMethodSubgraphState
    ) -> dict:
        user_query = state["user_query"]
        title = state["selected_policy_title"]
        what_to_verify = state["selected_policy_what_to_verify"]
        method = state["selected_policy_method"]
        llm_name = self.llm_mapping.generate_verification_method.llm_name

        prompt = (
            "ユーザーのクエリと選択された検証方針を基に、具体的な検証方法を詳細に出力してください。\n\n"
            f"ユーザーのクエリ: {user_query}\n\n"
            "選択された検証方針:\n"
            f"タイトル: {title}\n"
            f"検証内容: {what_to_verify}\n"
            f"手法: {method}\n\n"
            "出力:\n"
            "- 検証内容(4,5文): what_to_verify\n"
            "- 実験設定(実験番号をexperiment_id, 設定内容をdescriptionとしたリスト): experiment_settings\n"
            "- 手順(実験工程を順番にリスト): steps"
        )

        logger.info("Generating detailed verification method")

        result = await self.litellm_client.structured_output(
            llm_name=llm_name,
            message=prompt,
            data_model=VerificationMethodOutput,
        )

        logger.info("Verification method generated successfully")
        return {
            "what_to_verify": result.what_to_verify,
            "experiment_settings": {
                s.experiment_id: s.description for s in result.experiment_settings
            },
            "steps": result.steps,
        }

    def build_graph(self):
        graph_builder = StateGraph(
            GenerateVerificationMethodSubgraphState,
            input_schema=GenerateVerificationMethodSubgraphInputState,
            output_schema=GenerateVerificationMethodSubgraphOutputState,
        )

        graph_builder.add_node(
            "generate_verification_method", self._generate_verification_method
        )

        graph_builder.add_edge(START, "generate_verification_method")
        graph_builder.add_edge("generate_verification_method", END)

        return graph_builder.compile()
