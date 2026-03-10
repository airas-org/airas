# Contributing Guide

Thank you for considering contributing to this project.

## Contribution Requirements

Before submitting a pull request, please ensure that:

1. You have read and agreed to the Contributor License Agreement (CLA).
2. Your contribution complies with the project's coding standards.
3. All tests pass and relevant documentation is updated.

## Contributor License Agreement

This project requires all contributors to agree to the CLA.

By submitting a pull request, you confirm that:
- You agree to the terms of the CLA.
- You have the right to contribute the submitted code.

The CLA can be found here:
- [CLA.md](./CLA.md)

## Code Style and Static Analysis

This project enforces consistent code style and static analysis using the following tools:

- **Type checking**: `mypy --strict`
- **Formatter**: `ruff-format`
- **Linter**: `ruff`

Contributors are expected to ensure that all checks pass before submitting a pull request.

To enable automatic checks before each commit, please run:

```bash
pre-commit install
```

Pull requests that do not meet these requirements may be requested for revision or may not be merged.

## For Core Team

### MCP servers and Plugins
For core team development, we use the following. If you need access, please contact us and we will invite you to each service.

- [Vercel](https://vercel.com/docs/agent-resources/vercel-mcp#claude-code)

    ```bash
    claude mcp add --transport http vercel https://mcp.vercel.com
    ```

- [Railway](https://docs.railway.com/ai/mcp-server#claude-code)

    ```bash
    claude mcp add Railway npx @railway/mcp-server
    ```

- [Subframe](https://docs.subframe.com/guides/mcp-server#installation)

    ```bash
    claude plugin marketplace add https://github.com/SubframeApp/subframe && claude plugin install subframe@subframe
    ```

- [Supabase](https://supabase.com/docs/guides/getting-started/mcp)

    ```bash
    claude mcp add --scope project --transport http supabase "https://mcp.supabase.com/mcp"
    ```

- [Stripe](https://docs.stripe.com/mcp?locale=ja-JP&mcp-client=claudecode#connect)

    ```bash
    claude mcp add --transport http stripe https://mcp.stripe.com/
    ```
