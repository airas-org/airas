import json
import logging
import os
from typing import Any, Callable, Dict, Optional

from airas.features import (
    AnalyticSubgraph,
    CitationSubgraph,
    CreateCodeSubgraph,
    CreateExperimentalDesignSubgraph,
    CreateMethodSubgraph,
    FixCodeSubgraph,
    GitHubActionsExecutorSubgraph,
    GithubDownloadSubgraph,
    GithubUploadSubgraph,
    HtmlSubgraph,
    LatexSubgraph,
    PrepareRepositorySubgraph,
    ReadmeSubgraph,
    RetrieveCodeSubgraph,
    RetrievePaperFromQuerySubgraph,
    RetrieveRelatedPaperSubgraph,
    WriterSubgraph,
)

logger = logging.getLogger(__name__)


class E2EExecutor:
    """e2e.pyの処理を実行するサービス"""

    def __init__(self, data_dir: str = "/workspaces/airas/data"):
        self.data_dir = data_dir
        self.subgraphs: Dict[str, Any] = {}
        self._initialize_subgraphs()

    def _initialize_subgraphs(self):
        """サブグラフを初期化"""
        try:
            # デフォルト設定
            llm_name = "gemini-2.0-flash-001"
            scrape_urls = [
                "https://icml.cc/virtual/2024/papers.html?filter=title",
            ]

            # サブグラフの初期化
            self.subgraphs["prepare"] = PrepareRepositorySubgraph()
            self.subgraphs["retriever"] = RetrievePaperFromQuerySubgraph(
                llm_name=llm_name, save_dir=self.data_dir, scrape_urls=scrape_urls
            )
            self.subgraphs["retriever2"] = RetrieveRelatedPaperSubgraph(
                llm_name=llm_name, save_dir=self.data_dir, scrape_urls=scrape_urls
            )
            self.subgraphs["retriever3"] = RetrieveCodeSubgraph(llm_name=llm_name)
            self.subgraphs["creator"] = CreateMethodSubgraph(
                llm_name="o3-mini-2025-01-31"
            )
            self.subgraphs["creator2"] = CreateExperimentalDesignSubgraph(
                llm_name="o3-mini-2025-01-31"
            )
            self.subgraphs["coder"] = CreateCodeSubgraph()
            self.subgraphs["executor"] = GitHubActionsExecutorSubgraph(gpu_enabled=True)
            self.subgraphs["fixer"] = FixCodeSubgraph(llm_name="o3-mini-2025-01-31")
            self.subgraphs["analysis"] = AnalyticSubgraph("o3-mini-2025-01-31")
            self.subgraphs["writer"] = WriterSubgraph("o3-mini-2025-01-31")
            self.subgraphs["citation"] = CitationSubgraph(llm_name="o3-mini-2025-01-31")
            self.subgraphs["latex"] = LatexSubgraph("o3-mini-2025-01-31")
            self.subgraphs["readme"] = ReadmeSubgraph()
            self.subgraphs["html"] = HtmlSubgraph("o3-mini-2025-01-31")
            self.subgraphs["upload"] = GithubUploadSubgraph()
            self.subgraphs["download"] = GithubDownloadSubgraph()

            logger.info("All subgraphs initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing subgraphs: {e}")
            raise

    def save_state(self, state: Dict[str, Any], step_name: str, save_dir: str) -> str:
        """状態を保存"""
        filename = f"{step_name}.json"
        state_save_dir = os.path.join(self.data_dir, save_dir)
        os.makedirs(state_save_dir, exist_ok=True)
        filepath = os.path.join(state_save_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"State saved: {filepath}")
        return state_save_dir

    def load_state(self, file_path: str) -> Dict[str, Any]:
        """状態を読み込み"""
        with open(file_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        logger.info(f"State loaded: {file_path}")
        return state

    def retrieve_execution_subgraph_list(
        self, file_path: str, subgraph_name_list: list[str]
    ) -> list[str]:
        """実行対象のサブグラフリストを取得"""
        filename = os.path.basename(file_path)
        START_FROM_STEP = os.path.splitext(filename)[0]
        start_index = subgraph_name_list.index(START_FROM_STEP)
        subgraph_name_list = subgraph_name_list[start_index + 1 :]
        return subgraph_name_list

    def run_e2e_process(
        self,
        github_repository: str,
        branch_name: str,
        save_dir: str,
        file_path: Optional[str] = None,
        base_queries: Optional[list[str]] = None,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """e2e処理を実行"""
        try:
            # サブグラフの実行順序
            subgraph_name_list = [
                "retriever",
                "retriever2",
                "retriever3",
                "creator",
                "creator2",
                "coder",
                "executor",
                "fixer",
                "analysis",
                "writer",
                "citation",
                "latex",
                "readme",
                "html",
            ]

            if file_path:
                # 状態をロード
                state = self.load_state(file_path)
                # 実行対象のサブグラフリストを取得
                subgraph_name_list = self.retrieve_execution_subgraph_list(
                    file_path, subgraph_name_list
                )
            else:
                # 最初から実行
                state = {
                    "base_queries": base_queries or ["diffusion model"],
                    "github_repository": github_repository,
                    "branch_name": branch_name,
                }

            # 準備処理（e2e.pyと同じ）
            if not file_path:
                logger.info("Running prepare subgraph")
                state = self.subgraphs["prepare"].run(state)
                logger.info(f"Prepare completed. State keys: {list(state.keys())}")
                if progress_callback:
                    progress_callback(0.05, "prepare")

            total_steps = len(subgraph_name_list)

            for i, subgraph_name in enumerate(subgraph_name_list):
                try:
                    logger.info(f"Running subgraph: {subgraph_name}")
                    logger.info(f"Current state keys: {list(state.keys())}")

                    if progress_callback:
                        progress = (i + 1) / total_steps
                        progress_callback(progress, subgraph_name)

                    if subgraph_name == "retriever":
                        state = self.subgraphs["retriever"].run(state)
                        logger.info(
                            f"Retriever completed. State keys: {list(state.keys())}"
                        )
                        self.save_state(state, "retriever", save_dir)
                    elif subgraph_name == "retriever2":
                        # 必要なキーの存在を確認
                        if "base_method_text" not in state:
                            logger.error(
                                "base_method_text not found in state. Available keys: "
                                + str(list(state.keys()))
                            )
                            raise KeyError("base_method_text not found in state")
                        state = self.subgraphs["retriever2"].run(state)
                        self.save_state(state, "retriever2", save_dir)
                    elif subgraph_name == "retriever3":
                        state = self.subgraphs["retriever3"].run(state)
                        self.save_state(state, "retriever3", save_dir)
                    elif subgraph_name == "creator":
                        state = self.subgraphs["creator"].run(state)
                        self.save_state(state, "creator", save_dir)
                    elif subgraph_name == "creator2":
                        state = self.subgraphs["creator2"].run(state)
                        self.save_state(state, "creator2", save_dir)
                    elif subgraph_name == "coder":
                        state = self.subgraphs["coder"].run(state)
                        self.save_state(state, "coder", save_dir)
                    elif subgraph_name == "executor":
                        state = self.subgraphs["executor"].run(state)
                        self.save_state(state, "executor", save_dir)
                    elif subgraph_name == "fixer":
                        while True:
                            state = self.subgraphs["fixer"].run(state)
                            self.save_state(state, "fixer", save_dir)
                            if state.get("executed_flag") is True:
                                state = self.subgraphs["analysis"].run(state)
                                self.save_state(state, "analysis", save_dir)
                                break
                            else:
                                state = self.subgraphs["executor"].run(state)
                                self.save_state(state, "executor", save_dir)
                    elif subgraph_name == "analysis":
                        state = self.subgraphs["analysis"].run(state)
                        self.save_state(state, "analysis", save_dir)
                    elif subgraph_name == "writer":
                        state = self.subgraphs["writer"].run(state)
                        self.save_state(state, "writer", save_dir)
                    elif subgraph_name == "citation":
                        state = self.subgraphs["citation"].run(state)
                        self.save_state(state, "citation", save_dir)
                    elif subgraph_name == "latex":
                        state = self.subgraphs["latex"].run(state)
                        self.save_state(state, "latex", save_dir)
                    elif subgraph_name == "readme":
                        state = self.subgraphs["readme"].run(state)
                        self.save_state(state, "readme", save_dir)
                    elif subgraph_name == "html":
                        state = self.subgraphs["html"].run(state)
                        self.save_state(state, "html", save_dir)

                    logger.info(f"Completed subgraph: {subgraph_name}")

                except Exception as e:
                    logger.error(f"Error in subgraph {subgraph_name}: {e}")
                    logger.error(f"State at error: {state}")
                    raise

            logger.info("E2E process completed successfully")
            return state

        except Exception as e:
            logger.error(f"Error in E2E process: {e}")
            raise

    def run_e2e_async(
        self,
        job_id: str,
        github_repository: str,
        branch_name: str,
        save_dir: str,
        file_path: Optional[str] = None,
        base_queries: Optional[list[str]] = None,
        job_manager=None,
    ):
        """非同期でe2e処理を実行"""

        def progress_callback(progress: float, current_step: str):
            if job_manager:
                job_manager.update_job_status(
                    job_id,
                    "running",
                    progress=progress,
                    current_step=current_step,
                )

        try:
            # ジョブ開始
            if job_manager:
                job_manager.update_job_status(job_id, "running", progress=0.0)

            # 処理実行
            result = self.run_e2e_process(
                github_repository=github_repository,
                branch_name=branch_name,
                save_dir=save_dir,
                file_path=file_path,
                base_queries=base_queries,
                progress_callback=progress_callback,
            )

            # ジョブ完了
            if job_manager:
                job_manager.update_job_status(
                    job_id,
                    "completed",
                    progress=1.0,
                    result=result,
                )

        except Exception as e:
            logger.error(f"Error in async E2E process for job {job_id}: {e}")
            if job_manager:
                job_manager.update_job_status(
                    job_id,
                    "failed",
                    error=str(e),
                )
