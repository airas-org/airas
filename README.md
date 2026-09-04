<!-- Title Image Placeholder -->
# AIRAS - an open-source project for research automation

![Airas Logo](https://i.imgur.com/BNFAt17.png)

<p align="center">
  <a href="https://pypi.org/project/airas/">
    <img src="https://img.shields.io/pypi/v/airas" alt="PyPI" />
  </a>
  <a href="https://airas-org.github.io/airas/">
    <img src="https://img.shields.io/badge/Documentation-%F0%9F%93%95-blue" alt="Documentation" />
  </a>
  <a href="https://github.com/airas-org/airas/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License" />
  </a>
  <a href="https://discord.gg/ktumZQP3Tp">
    <img src="https://img.shields.io/badge/Discord-Join%20Us-7289da?logo=discord&logoColor=white" alt="Discord" />
  </a>
  <a href="https://x.com/fuyu_quant">
    <img src="https://img.shields.io/twitter/follow/fuyu_quant?style=social" alt="Twitter Follow" />
  </a>
</p>

AIRAS is open-source software for automated research. It gives a coding agent (Claude Code, Cursor, or any MCP client) everything it needs to take a research topic through literature survey, hypothesis, experiments, and a finished paper, and it makes the paper's claims **verifiable**: the paper is preregistered in git before any experiment runs, every reported number is realized from run outputs, and CI re-checks all of it before the PDF of record is produced.

AIRAS ships as one PyPI package (`airas`) that provides:

- an **MCP server** with 40+ research tools (paper search, hypothesis and experimental design, experiment execution on GitHub Actions or Seyval, figure rendering, LaTeX, Overleaf, paper reproduction, and the record/verification tools),
- a **Claude Code plugin** that bundles the server with the `auto-research` workflow skills,
- a small **CLI** (`airas verify-record`, `airas verify-paper`) that the experiment repository's CI uses as the verification gate.

Currently, it focuses on the automation of machine learning research.

## Quick Start

No clone, no Docker. Only [uv](https://docs.astral.sh/uv/) is required; `uvx` fetches the package on first run.

### 1. Install

**Claude Code plugin (recommended).** Installs the MCP server and the research-workflow skills in one step:

```
/plugin marketplace add airas-org/airas
/plugin install airas@airas
```

**Claude Code, MCP server only:**

```bash
claude mcp add airas -- uvx airas
```

**Other MCP clients.** Add the server to your client's MCP configuration (e.g. `.mcp.json`):

```json
{
  "mcpServers": {
    "airas": {
      "command": "uvx",
      "args": ["airas"]
    }
  }
}
```

### 2. Configure credentials

Credentials live in `~/.airas/credentials.json` and are re-read on every tool call, so you can create or edit the file at any time:

```bash
mkdir -p ~/.airas
cat > ~/.airas/credentials.json <<'EOF'
{
  "GH_PERSONAL_ACCESS_TOKEN": "ghp_...",
  "ANTHROPIC_API_KEY": "sk-ant-..."
}
EOF
chmod 600 ~/.airas/credentials.json
```

| Key | Purpose |
| --- | --- |
| `GH_PERSONAL_ACCESS_TOKEN` | Required. Creates and drives the experiment repository (`repo` + `workflow` scopes, admin on the repository). |
| One of `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` / `OPENROUTER_API_KEY` / `AWS_BEARER_TOKEN_BEDROCK` / `VERCEL_AI_GATEWAY_API_KEY` / `RIKYU_API_KEY` | Backend-LLM generation tools. Optional: the same steps can be authored by the MCP host itself via `get_generation_prompt`. |
| `SEYVAL_API_KEY` (+ optional `SEYVAL_COMPUTE_ID`) | Run experiments on the Seyval compute platform and enable the provenance cross-check. |

### 3. Start a research project

In Claude Code, invoke the orchestrator skill and give it a topic:

```
/airas:auto-research
```

It walks through the flow below, asking you to settle the operational choices (repository visibility, execution platform, compute target) once up front. Other MCP clients can start from the server's `start_research` prompt or call the tools directly.

## The auto-research flow

`auto-research` owns only the ordering and the rules that span steps. Each step is its own skill with a stated contract, so you can also invoke a single step on an existing repository.

| Step | Skill | What it leaves in the repository |
| --- | --- | --- |
| 1 | `setup-repository` | An experiment repository created from [airas-template](https://github.com/airas-org/airas-template), cloned, with Actions secrets provisioned and `main` protected. All research state lives here from now on. |
| 2 | `discover-papers` | A study list distilled from multi-source paper search, including [airas-papers-db](https://github.com/airas-org/airas-papers-db), and full-text reading. |
| 3 | `hypothesize-and-design` | A falsifiable hypothesis and an experimental design that fixes run ids, metrics, models, datasets, and the compute environment. |
| 4 | `preregister-paper` | The full paper, written **before any experiment**, as numbered claims with criteria and predicted intervals. Its commit is the freeze point; `.research/record.json` is created here. |
| 5 | `write-experiment-code` | Experiment code against a fixed execution contract (Hydra entrypoint, `sanity` / `pilot` / `full` modes), environment fixed by lockfile and Dockerfile. Metrics are produced by [airas-eval](https://github.com/airas-org/airas-eval), not by the code itself. |
| 6 | `run-experiments` | Runs executed on GitHub Actions or Seyval, outputs brought back under `.research/results/` with provenance. |
| 7 | `analyze-results` | The analysis and verifiable figures (Vega-Lite charts, text-defined diagrams). |
| 8 | `publish-paper` | Every stated number realized from the record, compile and verification green locally, then pushed. CI re-runs the verification and commits `paper.pdf` to the protected branch: the paper of record. |

### What the flow guarantees

- **Declare before you run.** Nothing is dispatched before the preregistration commit exists, and every run descends from it. Fixes are committed on top, never rebased away.
- **The record only grows.** `.research/record.json` is an append-only tree of hypotheses, claims, designs, runs, and results. A reworded claim, a changed run condition, or a dropped result all fail the same check. A claim that misses its criterion is reported as a negative result, not rewritten.
- **No experimental number is ever typed.** Numbers reach the paper only through `\airasval{...}` references to a run's measured metric or declared parameter, rendered from the record. Anything else is marked `\unverified{...}`.
- **The gate is enforced, not advisory.** Branch protection makes the verification workflow a required check, so a red run cannot be pushed past.
- **The repository is the state.** Everything a later step needs is committed, so a fresh session can resume from the clone alone.

### Execution platforms and LLMs

Experiments run on **GitHub Actions** (the runner repository's own workflows) or on the **Seyval** compute platform (managed or bring-your-own compute); `dispatch_experiment` selects the backend. Long-running steps return immediately and are polled with `get_workflow_runs` / `get_experiment_run_status`.

Generation steps are dual-mode. With a provider key they run on the backend LLM (`get_available_llms` lists the models your keys allow). Without one, `get_generation_prompt` hands the MCP host the same curated prompt and output schema so it can author the artifact itself. Supported providers: OpenAI, Anthropic, Google Gemini, OpenRouter, Amazon Bedrock, Vercel AI Gateway, and RIKEN R-CCS's Rikyu.

## Companion repositories

AIRAS relies on three sibling repositories under the `airas-org` organization. Each keeps one piece of the workflow outside the agent's reach.

| Repository | Role |
| --- | --- |
| [airas-template](https://github.com/airas-org/airas-template) | The template every experiment repository is created from. It ships the CI workflows, the execution contract, and the verification gate. |
| [airas-papers-db](https://github.com/airas-org/airas-papers-db) | A curated database of papers from top conferences that the agent can search through `search_papers`, alongside OpenAlex, Semantic Scholar, and arXiv. |
| [airas-eval](https://github.com/airas-org/airas-eval) | The evaluation logic, in one place. Metrics are computed by airas-eval from the run's evaluation inputs, not by the experiment code, so the agent cannot tamper with its own scores. |

## MCP tools

The server exposes tools for every phase; the skills above are thin contracts over them.

- **Discovery and design:** `generate_research_queries`, `search_papers`, `fetch_paper_fulltext`, `retrieve_papers`, `generate_hypothesis`, `generate_experimental_design`, `retrieve_models`, `retrieve_datasets`, `search_huggingface_hub`, `get_library_docs`
- **Repository and execution:** `prepare_repository`, `set_github_actions_secrets`, `protect_branch`, `dispatch_experiment`, `get_workflow_runs`, `get_experiment_run_status`, `fetch_experiment_results`, `import_run_outputs`, `download_workflow_artifacts`, `analyze_experiment`
- **Record and verification:** `preregister_record`, `append_to_record`, `update_record`, `verify_paper_values`
- **Figures and paper:** `render_chart`, `render_diagram`, `generate_bibfile`, `generate_paper`, `generate_latex`, `verify_latex`, `compile_latex`, `open_in_overleaf`
- **Paper reproduction:** `dispatch_paper_reproduction_generate`, `dispatch_paper_reproduction_run`, `fetch_paper_reproduction_results`, `dispatch_parameter_tuning_run`, `fetch_parameter_tuning_results`
- **Session and meta:** `upload_research_history`, `download_research_history`, `get_available_llms`, `get_generation_prompt`, `get_input_schema`

See the [MCP documentation](docs/development/MCP.mdx) for descriptions, credentials per tool, and configuration options.

## CLI

```bash
uvx airas                 # MCP server on stdio (default)
uvx airas verify-record   # check .research/record.json against run outputs, git history, and the platform
uvx airas verify-paper    # verify the paper's values and provenance and build its PDF (the CI gate)
```

`verify-record` and `verify-paper` are what the experiment repository's CI runs as the required check on the protected branch.

## Development

```bash
cd backend
uv sync
uv run airas
```

Lint and type checks are wired through `pre-commit` (`pre-commit install` once per clone). See [CONTRIBUTING.md](.github/CONTRIBUTING.md).

## Roadmap

AIRAS is developed in stages. Reliability comes first: an automated research pipeline is only worth scaling once its outputs can be trusted and reproduced.

**1. Reliability (in progress).** The record now guarantees that every number in the paper traces back to a declared run and its outputs, and CI enforces it. That covers the paper but not everything upstream of it: experiment code that games a benchmark, leaks test data, or deviates from the design still passes the gate. Closing that gap, from the experiment code and evaluation inputs back to the design, is the current focus.

- [x] Preregistration: claims, criteria, and predicted results frozen in git before any experiment runs
- [x] Append-only research record with numbers realized from run outputs and verified in CI
- [ ] Integrity of the experiment code and evaluation itself (benchmark hacking, data leakage, design deviation)

**2. Reproducibility.** When an agent drives the research, the agent's trajectory is part of the method. Keeping it, and being able to replay the workflow from it, is a necessary condition for a reproducible result.

- [ ] Persist the agent trajectory alongside the repository state
- [ ] Replay a research workflow from its recorded trajectory

**3. Research quality.** Once reliability and reproducibility are in place, raise the quality of the research itself: better hypotheses, stronger experimental designs, and more rigorous analysis.

**In parallel: other fields.** Machine learning is the first target because experiments are code. Alongside the stages above we are collaborating with other domains, such as life sciences, robotics, and materials science, to extend the same integrity model to their workflows.

## Contact

We aim to build an operating system for automated research that enables humanity to discover scientific breakthroughs it has not yet reached.

If you are interested in this topic, please feel free to contact us at <a href="mailto:ulti4929@gmail.com">ulti4929@gmail.com</a>.

## About AutoRes

This OSS is developed as part of the [AutoRes](https://www.autores.one/english) project.

## License

This project is licensed under the MIT License.
See the [LICENSE](./LICENSE) file for details.

## Contributions

By contributing to this project, you agree that your contributions are subject to the Contributor License Agreement (CLA) and may be used, modified, redistributed, and relicensed by the project owner, including for commercial, enterprise, and SaaS offerings.

See [CLA.md](.github/CLA.md) for details.

## Related projects

- [AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs) (Orchestra Research, MIT) — a library of library-specific ML engineering skills. AIRAS's experiment template installs it on code-generation runners so agents get framework-level guidance (fine-tuning, distributed training, inference); AIRAS's `get_library_docs` MCP tool complements it by pointing agents at each library's living documentation (`llms.txt` endpoints).

## Citation

If you use AIRAS in your research, please cite as follows:

```
@software{airas2025,
  author = {Toma Tanaka, Takumi Matsuzawa, Yuki Yoshino, Ilya Horiguchi, Shiro Takagi, Ryutaro Yamauchi, Wataru Kumagai},
  title = {AIRAS},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/airas-org/airas}
}
```
