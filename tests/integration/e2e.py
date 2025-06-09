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
import json
import os
from datetime import datetime

github_repository = "auto-res2/test-tanaka-v2"
branch_name = "develop"

pr = PrepareRepository()

input = {
    "github_repository": github_repository,
    "branch_name": branch_name,
}
result = pr.run(input)


state = {
    "base_queries": ["diffusion model"],
    "gpu_enabled": True,
    "experiment_iteration": 1
}

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

# Create a directory for saving states
state_save_dir = "/workspaces/airas/data/states"
os.makedirs(state_save_dir, exist_ok=True)

def save_state(state, step_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"state_{step_name}_{timestamp}.json"
    filepath = os.path.join(state_save_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"State saved: {filepath}")

# Run each step and save state
state = retriever.run(state)
save_state(state, "retriever")

state = retriever2.run(state)
save_state(state, "retriever2")

state = retriever3.run(state)
save_state(state, "retriever3")

state = creator.run(state)
save_state(state, "creator")

state = creator2.run(state)
save_state(state, "creator2")

state = coder.run(state)
save_state(state, "coder")

state = executor.run(state)
save_state(state, "executor")

state = fixer.run(state)
save_state(state, "fixer")

# if state["executed_flag"]:
#   continue

# anlysis = AnalyticSubgraph(llm_name="o3-mini-2025-01-31")
# state = anlysis.run(state)
