<!-- Title Image Placeholder -->
# AIRAS - an open-source project for research automation

![Airas Logo](https://i.imgur.com/BNFAt17.png)

<p align="center">
  <a href="https://pypi.org/project/airas/">
    <img src="https://img.shields.io/pypi/v/airas" alt="Documentation" />
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


AIRAS is an open-source software for automated research, being developed to support the entire research workflow. It aims to integrate all of the necessary functions for automating research—from literature search and method generation to experimentation and paper writing—and is designed with the aim of enabling as many individuals and organizations as possible to contribute to open innovation in research automation.

Features of AIRAS include:
- Implemented as individual research processes
- Allows users to add their own original research processes
- Enables saving implemented code and executing it on large-scale computational resources through advanced integration with GitHub
- Supports not only fully automated research, but also interactive research in which users can collaborate with the system

Currently, it focuses on the automation of machine learning research.

## Quick Start

Use AIRAS research tools (paper search, retrieval, hypothesis generation, experiment execution, paper writing) directly from an MCP client. No clone, no Docker — only [uv](https://docs.astral.sh/uv/) is required.

### Claude Code — plugin (recommended)

The plugin installs the MCP server **and** bundled research-workflow skills (`auto-research` for backend-LLM mode with API keys, `auto-research-claude-code` for key-free authoring by Claude Code itself) in one step:

```
/plugin marketplace add airas-org/airas
/plugin install airas@airas
```

### Claude Code — MCP server only

```bash
claude mcp add airas -- uvx airas
```

### Other MCP clients (mcp.json)

Add the following to your client's MCP configuration file (e.g. `.mcp.json`):

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

The server also exposes an MCP prompt, `start_research`, that walks any MCP client through the full research flow (in Claude Code: `/mcp__airas__start_research`).

See the [MCP documentation](docs/development/MCP.mdx) for the full tool list and configuration options.


## Roadmap

- [x] Complete automation of machine learning research with code-based experimentation
- [ ] Autonomous research in Research in simulated robotic environments
- [ ] Autonomous research in Real-world robotics research.
- [ ] Laboratory Automation and autonomous research in various fields

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

See [CLA.md](https://github.com/airas-org/airas/blob/main/README.md#contributions) for details.

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
