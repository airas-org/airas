"""仮説と実験設計。今は agent が skill（hypothesize-and-design）と
`get_generation_prompt` で自分で書くので、ここに関数はまだない。

TODO:
- 素朴にバックエンド LLM に作らせる入口。`mcp/tools/design.py` の
  `generate_hypothesis` / `generate_experimental_design` は今も
  `usecases/generators/` のサブグラフを呼んでいる。ここに
  `generate_hypothesis.py` / `generate_experimental_design.py` として
  素の関数を置き、`mcp/prompt_registry.py` と同じプロンプトを使う。
  判断材料（research_study_list、compute_environment）は引数で受ける。
- 探索アルゴリズムの取り込み（AI Scientist v2 の木探索など）。ループは
  `workflows/` のグラフに置き、node からここの関数と
  `usecases/literature` の `search_papers` / `fetch_paper_fulltext` を呼ぶ。
  record は `preregister_record` まで触らない。実験段階の木は展開ごとに
  `append_to_record` で design / run を追記してから dispatch し、LLM の
  判定は探索の指針までで verdict にはしない。
- `retrieve_models` / `retrieve_datasets`（`usecases/retrieve/` の
  サブグラフ）は設計の材料取得なのでここへ移す。
"""
