---
id: quickstart
title: クイックスタート
---

# クイックスタート

Research Graphをすぐに使い始めるための手順を説明します。

## インストール

```bash
pip install researchgraph
```

## 基本的な使い方

```python
from researchgraph.research_graph import ResearchGraph

# ResearchGraphのインスタンスを作成
research_graph = ResearchGraph()

# 論文URLを指定して処理を開始
result = research_graph.process("https://arxiv.org/abs/2310.12823")

# 結果を表示
print(result)
```

詳細な使用方法については、各コンポーネントのドキュメントをご参照ください。
