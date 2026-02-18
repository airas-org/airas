# AIRAS Quickstart

Run the AIRAS end-to-end autonomous research pipeline from any GitHub repository — no dedicated infrastructure required.

## What this workflow does

1. Checks out the `airas-org/airas` codebase and starts the backend server on `ubuntu-latest`
2. Submits your research topic to the pipeline
3. The pipeline automatically: searches papers → generates a hypothesis → designs experiments → generates & runs code → writes a paper → compiles LaTeX
4. The generated repository (code + paper) is pushed to your GitHub account

## What you need

| Secret | Required | Description |
|--------|----------|-------------|
| `GH_PERSONAL_ACCESS_TOKEN` | ✅ | GitHub PAT with `repo` + `workflow` scopes. If using a fine-grained token, set its lifetime to **366 days or less** (required by the `airas-org` enterprise policy). A classic PAT has no such restriction. |
| `ANTHROPIC_API_KEY` | ✅ (default) | Required for the default `github_actions_model` (`anthropic/claude-sonnet-4-5`). Can be replaced by another provider's key if you change that model. |
| `GEMINI_API_KEY` | ✅ (default) | Required for the default `primary_model` (`gemini-2.5-flash`). Can be replaced if you select a different primary model. |
| `OPENAI_API_KEY` | Optional | Required only when selecting an OpenAI model |
| `WANDB_API_KEY` | ✅ | Weights & Biases experiment tracking |
| `HF_TOKEN` | Optional | Hugging Face token (for gated models/datasets) |
| `LANGFUSE_SECRET_KEY` / `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_BASE_URL` | Optional | LLM observability with Langfuse |
| `AWS_BEARER_TOKEN_BEDROCK` | Optional | AWS Bedrock LLM access |
| `OPENROUTER_API_KEY` | Optional | OpenRouter LLM access |

## Setup

1. Copy [`examples/github_actions/airas_quickstart.yml`](examples/github_actions/airas_quickstart.yml) to your repository's `.github/workflows/` directory
2. Add the secrets above in your repository (`Settings → Secrets and variables → Actions → New repository secret`)
3. Go to **Actions → AIRAS Quickstart → Run workflow**

## Running the workflow

1. Navigate to **Actions → AIRAS Quickstart** in your repository
2. Click **Run workflow**
3. Fill in the inputs:
   - **Research topic** — the topic you want to investigate (required)
   - **GitHub owner** — leave empty to use your GitHub username
   - Other parameters have sensible defaults for standard GitHub-hosted runners
4. Click **Run workflow** to start

The pipeline will automatically search papers, generate a hypothesis, design and run experiments, and write a paper — pushing the results as a new repository to your GitHub account.

Progress can be monitored in the Actions log (step: `Poll for task completion`).

## Key parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `research_topic` | — | The research question to investigate |
| `github_owner` | your username | Owner of the generated repository |
| `repository_name` | auto-generated | Name of the generated repository (format: `airas-YYYYMMDD-HHMMSS`) |
| `branch_name` | `main` | Branch name in the generated repository |
| `is_github_repo_private` | `false` | Make the generated repository private |
| `runner_label` | `["ubuntu-latest"]` | Runner labels for experiment execution |
| `runner_description` | `GitHub Actions ubuntu-latest runner` | Description of the runner |
| `primary_model` | `gemini-2.5-flash` | LLM for hypothesis, writing, analysis |
| `paper_retrieval_model` | `gemini-2.5-flash` | LLM for paper search and summarization |
| `github_actions_agent` | `open_code` | Agent tool for experiment execution (`open_code` or `claude_code`) |
| `github_actions_model` | `anthropic/claude-sonnet-4-5` | LLM for experiment dispatch and LaTeX compilation |
| `num_paper_search_queries` | `2` | Number of paper search queries |
| `papers_per_query` | `3` | Number of papers retrieved per search query |
| `hypothesis_refinement_iterations` | `1` | Hypothesis refinement rounds |
| `num_experiment_models` | `1` | Number of models to evaluate |
| `num_experiment_datasets` | `1` | Number of datasets to use |
| `num_comparison_methods` | `1` | Comparison baselines |
| `paper_content_refinement_iterations` | `1` | Rounds of paper content refinement |
| `latex_template_name` | `mdpi` | LaTeX template (e.g. `mdpi`, `iclr2024`, `agents4science_2025`) |
| `wandb_entity` | — | W&B username or organization name (required) |

## Using the Claude Code agent (`claude_code`)

By default, `github_actions_agent` is set to `open_code`.
If you set it to `claude_code`, the experiment runner uses the [Claude Code GitHub App](https://github.com/apps/claude) instead.
This requires installing the Claude Code GitHub App on your repository before triggering the workflow.

## Runner time limits

The orchestration job (which starts the backend server and polls for completion) runs on `ubuntu-latest`. **GitHub-hosted runners have a 6-hour job time limit.** The full research pipeline can take longer depending on the topic and the number of iterations configured.

If you expect the run to exceed 6 hours, change `runs-on: ubuntu-latest` in `airas_quickstart.yml` to a self-hosted runner label.

## Running experiments on a GPU

By default the workflow runs experiments on `ubuntu-latest` (CPU only).
If you have access to a machine with a GPU, you can register it as a self-hosted runner on your GitHub repository and point the workflow to it:

1. Register your machine as a self-hosted runner in your repository
   (`Settings → Actions → Runners → New self-hosted runner`)
2. Assign labels to the runner (e.g. `self-hosted`, `gpu-runner`)
3. When triggering the workflow, set the inputs:
   - **`runner_label`**: `["self-hosted", "gpu-runner"]`
   - **`runner_description`**: description of your machine (e.g. `NVIDIA A100, VRAM: 80 GB`)

This allows experiments requiring GPU acceleration (larger models, longer training runs) to execute on your own hardware while the AIRAS orchestration still runs on `ubuntu-latest`.
