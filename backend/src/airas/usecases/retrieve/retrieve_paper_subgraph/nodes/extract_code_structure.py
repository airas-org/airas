"""Extract code structure from repository files for LLM-based file selection.

# Input Example (RepositoryContents):
# RepositoryContents(files=[
#     RepositoryFile(
#         path="src/model.py",
#         content='''
# \"\"\"Main model implementation.\"\"\"
# import torch
# import torch.nn as nn
#
# class TransformerModel(nn.Module):
#     \"\"\"Transformer-based model for sequence modeling.\"\"\"
#     def __init__(self, d_model, nhead):
#         super().__init__()
#         self.encoder = nn.TransformerEncoder(...)
#
#     def forward(self, x):
#         return self.encoder(x)
#
# def train_step(model, batch):
#     \"\"\"Execute a single training step.\"\"\"
#     ...
# ''',
#         extension=".py"
#     ),
#     RepositoryFile(
#         path="config/train.yaml",
#         content='''
# model:
#   d_model: 512
#   nhead: 8
# training:
#   batch_size: 32
#   lr: 0.001
# ''',
#         extension=".yaml"
#     ),
#     RepositoryFile(
#         path="README.md",
#         content='''
# # My Project
# ## Installation
# ## Usage
# ## Results
# ''',
#         extension=".md"
#     ),
# ])

# Output Example (RepositoryCodeStructure.to_prompt_string()):
# ## src/model.py
# Module: Main model implementation.
# Imports: torch
#   class TransformerModel(nn.Module)
#     "Transformer-based model for sequence modeling."
#     def __init__(d_model, nhead)
#     def forward(x)
#   def train_step(model, batch)
#     "Execute a single training step."
#
# ## config/train.yaml
# Keys: model, training
#
# ## README.md
# Sections: My Project, Installation, Usage, Results
"""

import ast
import json
import logging
import re
from dataclasses import dataclass, field

from airas.usecases.retrieve.retrieve_paper_subgraph.nodes.retrieve_repository_contents import (
    RepositoryContents,
    RepositoryFile,
)

logger = logging.getLogger(__name__)


@dataclass
class PythonFunctionStructure:
    name: str
    docstring: str | None = None
    args: list[str] = field(default_factory=list)
    is_method: bool = False


@dataclass
class PythonClassStructure:
    name: str
    docstring: str | None = None
    methods: list[PythonFunctionStructure] = field(default_factory=list)
    base_classes: list[str] = field(default_factory=list)


@dataclass
class PythonFileStructure:
    imports: list[str] = field(default_factory=list)
    classes: list[PythonClassStructure] = field(default_factory=list)
    functions: list[PythonFunctionStructure] = field(default_factory=list)
    module_docstring: str | None = None


@dataclass
class ConfigFileStructure:
    top_level_keys: list[str] = field(default_factory=list)


@dataclass
class MarkdownFileStructure:
    headings: list[str] = field(default_factory=list)


@dataclass
class FileCodeStructure:
    path: str
    extension: str
    python_structure: PythonFileStructure | None = None
    config_structure: ConfigFileStructure | None = None
    markdown_structure: MarkdownFileStructure | None = None


@dataclass
class RepositoryCodeStructure:
    files: list[FileCodeStructure] = field(default_factory=list)

    def to_prompt_string(self) -> str:
        lines = []

        for file_structure in self.files:
            lines.append(f"## {file_structure.path}")

            if file_structure.python_structure:
                ps = file_structure.python_structure
                if ps.module_docstring:
                    lines.append(f"Module: {ps.module_docstring[:200]}")
                if ps.imports:
                    lines.append(f"Imports: {', '.join(ps.imports[:20])}")
                for cls in ps.classes:
                    base_str = (
                        f"({', '.join(cls.base_classes)})" if cls.base_classes else ""
                    )
                    lines.append(f"  class {cls.name}{base_str}")
                    if cls.docstring:
                        lines.append(f'    "{cls.docstring[:100]}"')
                    for method in cls.methods:
                        args_str = ", ".join(method.args[:5])
                        lines.append(f"    def {method.name}({args_str})")
                for func in ps.functions:
                    args_str = ", ".join(func.args[:5])
                    lines.append(f"  def {func.name}({args_str})")
                    if func.docstring:
                        lines.append(f'    "{func.docstring[:100]}"')

            elif file_structure.config_structure:
                cs = file_structure.config_structure
                if cs.top_level_keys:
                    lines.append(f"Keys: {', '.join(cs.top_level_keys)}")

            elif file_structure.markdown_structure:
                ms = file_structure.markdown_structure
                if ms.headings:
                    lines.append(f"Sections: {', '.join(ms.headings[:10])}")

            lines.append("")

        return "\n".join(lines)


def _extract_python_structure(content: str) -> PythonFileStructure | None:
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        logger.warning(f"Failed to parse Python file: {e}")
        return None

    structure = PythonFileStructure()

    # Extract module docstring
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        structure.module_docstring = tree.body[0].value.value.strip()

    # Extract module-level imports only
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                structure.imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                structure.imports.append(node.module.split(".")[0])

    structure.imports = sorted(set(structure.imports))

    # Extract top-level classes and functions
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_structure = PythonClassStructure(
                name=node.name,
                docstring=ast.get_docstring(node),
                base_classes=[ast.unparse(base) for base in node.bases],
            )

            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    method_structure = PythonFunctionStructure(
                        name=item.name,
                        docstring=ast.get_docstring(item),
                        args=[arg.arg for arg in item.args.args if arg.arg != "self"],
                        is_method=True,
                    )
                    class_structure.methods.append(method_structure)
            structure.classes.append(class_structure)

        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            func_structure = PythonFunctionStructure(
                name=node.name,
                docstring=ast.get_docstring(node),
                args=[arg.arg for arg in node.args.args],
            )
            structure.functions.append(func_structure)

    return structure


def _extract_config_structure(
    content: str, extension: str
) -> ConfigFileStructure | None:
    structure = ConfigFileStructure()

    try:
        if extension in (".yaml", ".yml"):
            for line in content.split("\n"):
                if line and not line.startswith((" ", "\t", "#", "-")):
                    match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*):", line)
                    if match:
                        structure.top_level_keys.append(match.group(1))

        elif extension == ".json":
            data = json.loads(content)
            if isinstance(data, dict):
                structure.top_level_keys = list(data.keys())[:30]

        elif extension == ".toml":
            seen_section = False
            for line in content.split("\n"):
                match = re.match(r"^\[([^\]]+)\]", line)
                if match:
                    structure.top_level_keys.append(match.group(1))
                    seen_section = True
                elif (
                    not seen_section
                    and not line.startswith((" ", "\t", "#"))
                    and "=" in line
                ):
                    key = line.split("=")[0].strip()
                    if key:
                        structure.top_level_keys.append(key)

    except Exception as e:
        logger.warning(f"Failed to parse config file: {e}")
        return None

    return structure if structure.top_level_keys else None


def _extract_markdown_structure(content: str) -> MarkdownFileStructure | None:
    structure = MarkdownFileStructure()

    for line in content.split("\n"):
        match = re.match(r"^(#{1,3})\s+(.+)", line)
        if match:
            structure.headings.append(match.group(2).strip())

    return structure if structure.headings else None


def _extract_file_code_structure(file: RepositoryFile) -> FileCodeStructure:
    structure = FileCodeStructure(path=file.path, extension=file.extension)

    if file.extension == ".py":
        structure.python_structure = _extract_python_structure(file.content)

    elif file.extension in (".yaml", ".yml", ".json", ".toml"):
        structure.config_structure = _extract_config_structure(
            file.content, file.extension
        )

    elif file.extension == ".md":
        structure.markdown_structure = _extract_markdown_structure(file.content)

    return structure


def extract_repository_code_structure(
    contents: RepositoryContents,
) -> RepositoryCodeStructure:
    code_structure = RepositoryCodeStructure()

    for file in contents.files:
        file_structure = _extract_file_code_structure(file)
        code_structure.files.append(file_structure)

    return code_structure
