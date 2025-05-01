---
id: html-uploader
title: HTML uploader
sidebar_position: 3
---

# HTML Uploader Subgraph

このページではHTML Uploader Subgraphの詳細について説明します。

## 概要

HTML Uploader Subgraphは、研究論文からHTMLコンテンツを処理しアップロードすることを担当するコンポーネントです。

## 機能

- 主な機能1
- 主な機能2
- 主な機能3

## 使用方法

```python
import glob
from researchgraph.html_subgraph.html_subgraph import HtmlConverter

figures_dir = f"{save_dir}/images"
pdf_files = glob.glob(os.path.join(figures_dir, "*.pdf"))

extra_files = [
    {
        "upload_branch": "gh-pages",
        "upload_dir": "branches/{{ branch_name }}/",
        "local_file_paths": [f"{save_dir}/index.html"],
    },
    {
        "upload_branch": "gh-pages",
        "upload_dir": "branches/{{ branch_name }}/images/",
        "local_file_paths": pdf_files,
    },
]

html_converter = HtmlConverter(
    github_repository=github_repository,
    branch_name=branch_name,
    extra_files=extra_files,
    llm_name="o3-mini-2025-01-31",
    save_dir=save_dir,
)

result = html_converter.run()
print(f"result: {result}")
```

## API

HTML Uploader Subgraphが提供するAPIの詳細については準備中です。
