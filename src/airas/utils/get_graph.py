import os
from IPython.display import Image
from langgraph.graph.graph import CompiledGraph

from airas.research_graph import ResearchGraph

from airas.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraph,
)
from airas.generator_subgraph.generator_subgraph import GeneratorSubgraph
from airas.experimental_plan_subgraph.experimental_plan_subgraph import (
    ExperimentalPlanSubgraph,
)
from airas.executor_subgraph.executor_subgraph import ExecutorSubgraph
from airas.writer_subgraph.writer_subgraph import WriterSubgraph
from airas.upload_subgraph.upload_subgraph import UploadSubgraph

IMAGE_SAVE_DIR = "/workspaces/researchgraph/images"

save_dir = "/workspaces/researchgraph/data"
llm_name = "gpt-4o-mini-2024-07-18"
scrape_urls = [
    "https://icml.cc/virtual/2024/papers.html?filter=title",
    "https://iclr.cc/virtual/2024/papers.html?filter=title",
    # "https://nips.cc/virtual/2024/papers.html?filter=title",
    # "https://cvpr.thecvf.com/virtual/2024/papers.html?filter=title",
    # "https://eccv.ecva.net/virtual/2024/papers.html?filter=title",
]


def make_image(
    graph: CompiledGraph, file_name: str, image_save_dir: str = IMAGE_SAVE_DIR
):
    image = Image(graph.get_graph(xray=2).draw_mermaid_png())
    with open(os.path.join(image_save_dir, file_name), "wb") as f:
        f.write(image.data)


def print_mermaid(graph):
    print(graph.get_graph(xray=2).draw_mermaid())


def retrieve_paper_subgraph():
    graph = RetrievePaperSubgraph(
        llm_name=llm_name,
        save_dir=save_dir,
        scrape_urls=scrape_urls,
        add_paper_num=3,
    ).build_graph()
    make_image(graph, "retrieve_paper_subgraph.png")
    print_mermaid(graph)
    return


def generator_subgraph():
    graph = GeneratorSubgraph().build_graph()
    make_image(graph, "generator_subgraph.png")
    # print_mermaid(graph)
    return


def experimental_plan_subgraph():
    graph = ExperimentalPlanSubgraph().build_graph()
    make_image(graph, "experimental_plan_subgraph.png")
    print_mermaid(graph)
    return


def executor_subgraph():
    graph = ExecutorSubgraph(
        github_owner="auto-res2",
        repository_name="auto-research",
        save_dir=save_dir,
        max_code_fix_iteration=3,
    ).build_graph()
    make_image(graph, "executor_subgraph.png")
    print_mermaid(graph)
    return


def writer_subgraph():
    graph = WriterSubgraph(
        llm_name=llm_name,
        save_dir=save_dir,
    ).build_graph()
    make_image(graph, "writer_subgraph.png")
    print_mermaid(graph)
    return


def upload_subgraph():
    graph = UploadSubgraph(
        github_owner="auto-res2",
        repository_name="auto-research",
        save_dir=save_dir,
    ).build_graph()
    make_image(graph, "upload_subgraph.png")
    print_mermaid(graph)
    return


def research_graph():
    graph = ResearchGraph(
        save_dir=save_dir,
        scrape_urls=scrape_urls,
        add_paper_num=3,
        max_code_fix_iteration=3,
        repository="auto-res2/auto-research",
    ).build_graph()
    make_image(graph, "research_graph.png")
    print_mermaid(graph)
    return


if __name__ == "__main__":
    # retrieve_paper_subgraph()
    generator_subgraph()
    # experimental_plan_subgraph()
    # executor_subgraph()
    # writer_subgraph()
    # upload_subgraph()
    # research_graph()
