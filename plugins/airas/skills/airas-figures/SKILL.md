---
name: airas-figures
description: Create publication-quality result figures and method diagrams for an AIRAS research project — Vega-Lite charts via render_chart, text-notation diagrams (mermaid/graphviz/d2) via render_diagram, and the repository conventions that get them into the paper. Use when making charts, plots, or diagrams for an AIRAS experiment repository, or when figures are missing from the compiled paper.
---

# AIRAS figures and diagrams

Figures are authored by you, locally, and flow into the paper through
repository conventions — no copy step is needed.

## Result charts: `render_chart`

Build a Vega-Lite JSON spec from the experiment results (inline the data
under `data.values`) and call `render_chart(vega_lite_spec, output_path)`.
Rendering is fully local (vl-convert); no data leaves the machine and no
API keys are required. Prefer PDF output for papers.

## Method diagrams: `render_diagram`

Write the diagram as text (`diagram_type`: "mermaid", "graphviz", "d2",
"plantuml", and 20+ more Kroki notations) and call
`render_diagram(diagram_type, diagram_source, output_path)`. Uses the
public https://kroki.io by default; set `KROKI_BASE_URL` to a self-hosted
instance to keep unpublished diagrams private. For vector text in PDFs
prefer "graphviz"/"plantuml"; mermaid falls back to raster automatically.

## Where to save (in your local clone of the experiment repository)

- Charts: `.research/results/chart/<name>.pdf`
- Diagrams: `.research/results/diagram/<name>.pdf`
- Keep filenames unique across both directories.
- Commit and push with git.

## How they reach the paper

`compile_latex` and `open_in_overleaf` automatically collect every figure
PDF under `.research/results/` (and legacy `.research/diagrams/`) into the
paper's `images/` directory with the directory structure preserved.
Reference them in LaTeX as `images/<path relative to .research/results/>`,
e.g. `.research/results/chart/loss.pdf` → `images/chart/loss.pdf`.

Figures generated any other way (e.g. matplotlib from experiment code)
follow the same conventions — only the output location matters.
