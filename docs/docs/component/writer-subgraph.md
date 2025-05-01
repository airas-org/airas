---
sidebar_position: 11
---

# Writer Subgraph

This page explains the details of the Writer Subgraph.

## Overview

The Writer Subgraph is a component responsible for document generation and writing assistance.

## Features

- Main feature 1
- Main feature 2
- Main feature 3

## Usage

```python
# Example usage of Writer Subgraph
# To be implemented
```

# PaperWriter Usage

To use the PaperWriter module:

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

Details about the API provided by the Writer Subgraph are under preparation.
