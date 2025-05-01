# Retriever Usage

To use the Retriever module:

```python
from researchgraph.retrieve_paper_subgraph.retrieve_paper_subgraph import Retriever

scrape_urls = [
    "https://icml.cc/virtual/2024/papers.html?filter=title",
    "https://iclr.cc/virtual/2024/papers.html?filter=title",
]
add_paper_num = 1

retriever = Retriever(
    github_repository=github_repository,
    branch_name=branch_name,
    llm_name="o3-mini-2025-01-31",
    save_dir=save_dir,
    scrape_urls=scrape_urls,
    add_paper_num=add_paper_num,
)

retriever_input = {
    "queries": ["diffusion model"],
}

result = retriever.run(retriever_input)
print(result)
```
