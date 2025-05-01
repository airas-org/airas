---
id: executor
title: Executor
sidebar_position: 2
---

# Executor Subgraph

This page explains the details of the Executor Subgraph.

## Overview

The Executor Subgraph is a component responsible for executing code and running experiments from research papers.

## Features

- Main feature 1
- Main feature 2
- Main feature 3

## Usage

To use the Executor module:

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

Details about the API provided by the Executor Subgraph are under preparation.
