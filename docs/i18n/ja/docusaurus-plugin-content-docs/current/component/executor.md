---
id: executor
title: Executor
sidebar_position: 2
---

# Executor サブグラフ

このページでは Executor サブグラフの詳細について説明します。

## 概要

Executor サブグラフは、論文のコード実行や実験の実行を担うコンポーネントです。

## 主な機能

- 主な機能1
- 主な機能2
- 主な機能3

## 使い方

```python
from researchgraph.executor_subgraph.executor_subgraph import Executor

max_code_fix_iteration = 3

executor = Executor(
    github_repository=github_repository,
    branch_name=branch_name,
    save_dir=save_dir,
    max_code_fix_iteration=max_code_fix_iteration,
)

result = executor.run()
print(f"result: {result}")
```

## API

APIの詳細は準備中です。
