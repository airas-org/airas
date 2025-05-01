---
id: html-uploader
title: HTML uploader
sidebar_position: 3
---

# HTML Uploader Subgraph

This page explains the details of the HTML Uploader Subgraph.

## Overview

The HTML Uploader Subgraph is a component responsible for processing and uploading HTML content from research papers.

## Features

- Main feature 1
- Main feature 2
- Main feature 3

## Usage

```python
# Example usage of HTML Uploader Subgraph
# To be implemented
```

## API

Details about the API provided by the HTML Uploader Subgraph are under preparation.

# HtmlConverter Usage

To use the HtmlConverter module:

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
