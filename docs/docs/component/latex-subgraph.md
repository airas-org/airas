---
sidebar_position: 7
---

# LaTeX Subgraph

This page explains the details of the LaTeX Subgraph.

## Overview

The LaTeX Subgraph is a component responsible for processing LaTeX formats of papers and documents.

## Features

- Main feature 1
- Main feature 2
- Main feature 3

## Usage

```python
# Example usage of LaTeX Subgraph
# To be implemented
```

# LatexConverter Usage

To use the LatexConverter module:

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

Details about the API provided by the LaTeX Subgraph are under preparation.
