import asyncio
import logging
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLM_CONFIG, NodeLLMConfig
from airas.core.logging_utils import setup_logging
from airas.infra.litellm_client import LiteLLMClient

setup_logging()
logger = logging.getLogger(__name__)


def record_execution_time(f):
    return time_node("propose_verification_policy_subgraph")(f)  # noqa: E731


class FeasibilityOutput(BaseModel):
    result: Literal[0, 1]
    reason: str


class PolicySummariesOutput(BaseModel):
    summaries: list[str]


class DetailedMethodOutput(BaseModel):
    title: str
    what_to_verify: str
    method: str
    pros: list[str]
    cons: list[str]


class ProposeVerificationPolicyLLMMapping(BaseModel):
    propose_verification_policy: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "propose_verification_policy"
    ]


class ProposeVerificationPolicySubgraphInputState(TypedDict):
    user_query: str


class ProposeVerificationPolicySubgraphOutputState(ExecutionTimeState):
    feasible: bool
    feasibility_reason: str | None
    policy_summaries: list[str]
    proposed_methods: list[dict[str, Any]]


class ProposeVerificationPolicySubgraphState(
    ProposeVerificationPolicySubgraphInputState,
    ProposeVerificationPolicySubgraphOutputState,
    total=False,
):
    pass


class ProposeVerificationPolicySubgraph:
    def __init__(
        self,
        litellm_client: LiteLLMClient,
        llm_mapping: ProposeVerificationPolicyLLMMapping | None = None,
    ):
        self.litellm_client = litellm_client
        self.llm_mapping = llm_mapping or ProposeVerificationPolicyLLMMapping()

    @record_execution_time
    async def _generate_policy_options(
        self, state: ProposeVerificationPolicySubgraphState
    ) -> dict:
        user_query = state["user_query"]
        llm_name = self.llm_mapping.propose_verification_policy.llm_name

        feasibility_prompt = (
            "判定基準: 計算機環境の中で実行できる実験かどうか。"
            "0=実行不可, 1=実行可能。理由を添えて答えてください。\n\n"
            f"ユーザーのクエリ: {user_query}"
        )
        policy_summaries_prompt = (
            "以下のユーザーのクエリを検証するための方針を3パターン、"
            "それぞれ1文で出力してください。\n\n"
            f"ユーザーのクエリ: {user_query}"
        )

        logger.info("Running feasibility check and policy generation in parallel")

        feasibility_result, policy_summaries_result = await asyncio.gather(
            self.litellm_client.structured_output(
                llm_name=llm_name,
                message=feasibility_prompt,
                data_model=FeasibilityOutput,
            ),
            self.litellm_client.structured_output(
                llm_name=llm_name,
                message=policy_summaries_prompt,
                data_model=PolicySummariesOutput,
            ),
        )

        if feasibility_result.result == 0:
            logger.info(f"Feasibility check failed: {feasibility_result.reason}")
            return {
                "feasible": False,
                "feasibility_reason": feasibility_result.reason,
                "policy_summaries": [],
            }

        logger.info("Feasibility check passed, policy summaries generated")
        return {
            "feasible": True,
            "feasibility_reason": None,
            "policy_summaries": policy_summaries_result.summaries,
        }

    @record_execution_time
    async def _generate_detailed_methods(
        self, state: ProposeVerificationPolicySubgraphState
    ) -> dict:
        user_query = state["user_query"]
        policy_summaries = state.get("policy_summaries", [])
        llm_name = self.llm_mapping.propose_verification_policy.llm_name

        logger.info(
            f"Generating detailed methods for {len(policy_summaries)} policies in parallel"
        )

        async def generate_method(policy: str) -> DetailedMethodOutput:
            prompt = (
                "ユーザーのクエリと検証方針を基に、具体的な検証方法を詳細に出力してください。\n\n"
                f"ユーザーのクエリ: {user_query}\n\n"
                f"検証方針: {policy}\n\n"
                "出力:\n"
                "- 検証内容(1,2文): whatToVerify\n"
                "- 手法(1,2文): method\n"
                "- Pros(短文リスト): pros\n"
                "- Cons(短文リスト): cons\n"
                "- タイトル(10文字程度): title"
            )
            return await self.litellm_client.structured_output(
                llm_name=llm_name,
                message=prompt,
                data_model=DetailedMethodOutput,
            )

        results = await asyncio.gather(
            *[generate_method(policy) for policy in policy_summaries]
        )

        proposed_methods = [
            {
                "id": str(i),
                "title": result.title,
                "what_to_verify": result.what_to_verify,
                "method": result.method,
                "pros": result.pros,
                "cons": result.cons,
            }
            for i, result in enumerate(results)
        ]

        logger.info(f"Generated {len(proposed_methods)} detailed methods")
        return {"proposed_methods": proposed_methods}

    def _should_generate_methods(
        self, state: ProposeVerificationPolicySubgraphState
    ) -> str:
        if not state.get("feasible", True):
            return END
        return "generate_detailed_methods"

    def build_graph(self):
        graph_builder = StateGraph(
            ProposeVerificationPolicySubgraphState,
            input_schema=ProposeVerificationPolicySubgraphInputState,
            output_schema=ProposeVerificationPolicySubgraphOutputState,
        )

        graph_builder.add_node("generate_policy_options", self._generate_policy_options)
        graph_builder.add_node(
            "generate_detailed_methods", self._generate_detailed_methods
        )

        graph_builder.add_edge(START, "generate_policy_options")
        graph_builder.add_conditional_edges(
            "generate_policy_options",
            self._should_generate_methods,
        )
        graph_builder.add_edge("generate_detailed_methods", END)

        return graph_builder.compile()
