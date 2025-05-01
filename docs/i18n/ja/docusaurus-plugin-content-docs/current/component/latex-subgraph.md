---
sidebar_position: 7
---

# LaTeX Subgraph

このページではLaTeX Subgraphの詳細について説明します。

## 概要

LaTeX Subgraphは論文やドキュメントのLaTeXフォーマットに関する処理を担当するコンポーネントです。

## 機能

- 主な機能1
- 主な機能2
- 主な機能3

## 使用方法

```python
from researchgraph.latex_subgraph.latex_subgraph import LatexConverter

extra_files = [
    {
        "upload_branch": "{{ branch_name }}",
        "upload_dir": ".research/",
        "local_file_paths": [f"{save_dir}/paper.pdf"],
    }
]

latex_converter = LatexConverter(
    github_repository=github_repository,
    branch_name=branch_name,
    extra_files=extra_files,
    llm_name="o3-mini-2025-01-31",
    save_dir=save_dir,
)

result = latex_converter.run({})
print(f"result: {result}")
```

## API

LaTeX Subgraphが提供するAPIの詳細については準備中です。
