---
id: local-setup
title: ローカル環境のセットアップ
---

# ローカル環境のセットアップ

Research Graphの開発環境を構築するための手順を説明します。

## 前提条件

- Python 3.9以上
- Git
- 各種依存ライブラリ

## インストール手順

1. リポジトリのクローン：

```bash
git clone https://github.com/auto-res/researchgraph.git
cd researchgraph
```

2. 開発環境のセットアップ：

```bash
pip install -e ".[dev]"
```

3. 開発サーバーの起動：

```bash
# 必要に応じてサービスを起動
```

## テストの実行

```bash
pytest
```

詳細な開発ガイドラインについては、GitHubのREADMEをご参照ください。
