"""AIRAS command-line entry point.

- `airas` (no arguments): run the MCP server on stdio. Kept as the default
  so existing MCP client registrations (`claude mcp add airas -- uvx airas`)
  keep working.
- `airas mcp`: run the MCP server explicitly.
- `airas dashboard`: serve the web dashboard (FastAPI API + bundled
  frontend) on localhost.
"""

import argparse
import threading
import webbrowser

# "AIRAS" on a phone keypad (per ITU-T E.161); a high port to avoid the
# crowded 8000 range.
DEFAULT_DASHBOARD_PORT = 24727


def _run_mcp() -> None:
    from airas.mcp.server import main as mcp_main

    mcp_main()


def _run_dashboard(host: str, port: int, open_browser: bool) -> None:
    import uvicorn

    if open_browser:
        url = (
            f"http://{'localhost' if host in ('0.0.0.0', '127.0.0.1') else host}:{port}"
        )
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()

    uvicorn.run("airas.dashboard.api.main:app", host=host, port=port)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="airas",
        description="AIRAS: automated AI research toolkit",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("mcp", help="Run the MCP server on stdio (default)")

    dashboard = subparsers.add_parser("dashboard", help="Serve the web dashboard")
    dashboard.add_argument("--host", default="127.0.0.1", help="Bind address")
    dashboard.add_argument(
        "--port",
        type=int,
        default=DEFAULT_DASHBOARD_PORT,
        help=f"Port to listen on (default: {DEFAULT_DASHBOARD_PORT})",
    )
    dashboard.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the dashboard in a browser",
    )

    args = parser.parse_args()

    if args.command == "dashboard":
        _run_dashboard(args.host, args.port, open_browser=not args.no_browser)
    else:
        # No subcommand (or `mcp`): stdio MCP server, the historical default.
        _run_mcp()


if __name__ == "__main__":
    main()
