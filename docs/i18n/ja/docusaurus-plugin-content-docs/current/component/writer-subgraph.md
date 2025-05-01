---
sidebar_position: 11
---

# Writer サブグラフ

このページでは Writer サブグラフの詳細について説明します。

## 概要

Writer サブグラフは、論文執筆やドキュメント生成を担うコンポーネントです。

## 主な機能

- 主な機能1
- 主な機能2
- 主な機能3

## 使い方

```python
from researchgraph.writer_subgraph.writer_subgraph import PaperWriter

refine_round = 1

paper_writer = PaperWriter(
    github_repository=github_repository,
    branch_name=branch_name,
    llm_name="o3-mini-2025-01-31",
    save_dir=save_dir,
    refine_round=refine_round,
)

result = paper_writer.run({})
print(f"result: {result}")
```

## API

APIの詳細は準備中です。
