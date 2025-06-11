from airas.preparation import PrepareRepository
from airas.retrieve import (
  RetrieveCodeSubgraph, 
  RetrievePaperFromQuerySubgraph, 
  RetrieveRelatedPaperSubgraph
)
from airas.create import (
  CreateExperimentalDesignSubgraph, 
  CreateMethodSubgraph
)
from airas.execution import (
  ExecutorSubgraph, 
  FixCodeSubgraph, 
  PushCodeSubgraph
)
from airas.analysis import AnalyticSubgraph
from airas.write import WriterSubgraph, CitationSubgraph
import json
import os
from datetime import datetime


scrape_urls = [
    "https://icml.cc/virtual/2024/papers.html?filter=title",
    # "https://iclr.cc/virtual/2024/papers.html?filter=title",
    # "https://nips.cc/virtual/2024/papers.html?filter=title",
    # "https://cvpr.thecvf.com/virtual/2024/papers.html?filter=title",
]
llm_name = "o3-mini-2025-01-31"
save_dir = "/workspaces/airas/data"

retriever = RetrievePaperFromQuerySubgraph(llm_name=llm_name, save_dir=save_dir, scrape_urls=scrape_urls)
retriever2 = RetrieveRelatedPaperSubgraph(llm_name=llm_name, save_dir=save_dir, scrape_urls=scrape_urls)
retriever3 = RetrieveCodeSubgraph(llm_name=llm_name)
creator = CreateMethodSubgraph(llm_name=llm_name)
creator2 = CreateExperimentalDesignSubgraph(llm_name=llm_name)
coder = PushCodeSubgraph()
executor = ExecutorSubgraph()
fixer = FixCodeSubgraph(llm_name=llm_name)
analysis = AnalyticSubgraph(llm_name)
writer = WriterSubgraph(llm_name)
citation = CitationSubgraph(llm_name=llm_name)


def save_state(state, step_name):
    state_save_dir = "/workspaces/airas/data/states"
    os.makedirs(state_save_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"state_{step_name}_{timestamp}.json"
    filepath = os.path.join(state_save_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"State saved: {filepath}")
    return


def load_state(filename):
    state_save_dir = "/workspaces/airas/data/states"
    os.makedirs(state_save_dir, exist_ok=True)
    filepath = os.path.join(state_save_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        state = json.load(f)
    print(f"State loaded: {filepath}")
    return state


def retrieve_execution_subgraph_list(filename: str, subgraph_name_list: list[str]) -> list[str]:
    START_FROM_STEP = filename.split('_')[1]
    start_index = subgraph_name_list.index(START_FROM_STEP)
    subgraph_name_list = subgraph_name_list[start_index + 1:]
    return subgraph_name_list


def run_from_state_file(github_repository, branch_name, filename: str | None = None):
    """
    filenameが指定されていればそのstateファイルから、指定されていなければ最初からsubgraphを順次実行し、各ステップの結果を保存する
    """
    subgraph_name_list = [
        "retriever",
        "retriever2",
        "retriever3",
        "creator",
        "creator2",
        "coder",
        "executor",
        "fixer",
        "anlysis",
        "writer",
        "citation",
    ]

    if filename:
        # stateをロード
        state = load_state(filename)
        # 実行対象のsubgraphリストを取得
        subgraph_name_list = retrieve_execution_subgraph_list(filename, subgraph_name_list)
    else:
        # 最初から実行
        state = {
            "base_queries": ["diffusion model"],
            "gpu_enabled": True,
            "experiment_iteration": 1,
            "github_repository": github_repository,
            "branch_name": branch_name,
        }

    for subgraph_name in subgraph_name_list:
        if subgraph_name == "retriever":
            state = retriever.run(state)
            save_state(state, "retriever")
        elif subgraph_name == "retriever2":
            state = retriever2.run(state)
            save_state(state, "retriever2")
        elif subgraph_name == "retriever3":
            state = retriever3.run(state)
            save_state(state, "retriever3")
        elif subgraph_name == "creator":
            state = creator.run(state)
            save_state(state, "creator")
        elif subgraph_name == "creator2":
            state = creator2.run(state)
            save_state(state, "creator2")
        elif subgraph_name == "coder":
            state = coder.run(state)
            save_state(state, "coder")
        elif subgraph_name == "executor":
            state = executor.run(state)
            save_state(state, "executor")
        elif subgraph_name == "fixer":
            while True:
                state = fixer.run(state)
                save_state(state, "fixer")
                if state.get("executed_flag") is True:
                    state = analysis.run(state)
                    save_state(state, "analysis")
                    break
                else:
                    state = executor.run(state)
                    save_state(state, "executor")
        elif subgraph_name == "analysis":
            state = analysis.run(state)
            save_state(state, "analysis")
        elif subgraph_name == "writer":
            state = writer.run(state)
            save_state(state, "writer")
        elif subgraph_name == "citation":
            state = citation.run(state)
            save_state(state, "citation")
        

if __name__ == "__main__":
    github_repository = "auto-res2/test-tanaka-v6"
    branch_name = "develop-1"
    
    # リポジトリの用意
    PrepareRepository(
        github_repository=github_repository,
        branch_name=branch_name,
    ).run()
    
    
    # file_name = "state_coder_20250610_160554.json"
    # run_from_state_file(github_repository, branch_name, file_name)
    run_from_state_file(github_repository, branch_name)

    # import sys
    # if len(sys.argv) > 1:
    #     run_from_state_file(sys.argv[1])
    # else:
    #     run_from_state_file()
