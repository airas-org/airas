import argparse
import asyncio
import json
import sys
import threading
import webbrowser
from pathlib import Path

from airas.usecases.publication.verify_paper import detect_templates, verify_paper
from airas.usecases.recording.verify_record import verify_record

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


def _run_verify_paper(args: argparse.Namespace) -> None:
    templates = args.template or detect_templates(args.local_path)
    if not templates:
        print(
            "No paper found: no known template under .research/latex/ has a main.tex",
            file=sys.stderr,
        )
        sys.exit(2)

    out = Path(args.output_dir).expanduser().resolve()
    results = [
        asyncio.run(
            verify_paper(
                args.local_path,
                template,
                pdf_path=str(out / f"{template}.pdf"),
                check_provenance=not args.no_provenance,
                require_record=not args.no_require_paper_values,
                require_provenance=not (
                    args.no_provenance or args.allow_unavailable_provenance
                ),
                require_history=not args.allow_unavailable_history,
            )
        )
        for template in templates
    ]
    print(json.dumps([r.model_dump() for r in results], indent=2, ensure_ascii=False))
    sys.exit(0 if all(r.ok for r in results) else 1)


def _run_verify_record(args: argparse.Namespace) -> None:
    record = asyncio.run(
        verify_record(
            args.local_path,
            check_provenance=not args.no_provenance,
            require_provenance=not (
                args.no_provenance or args.allow_unavailable_provenance
            ),
            require_history=not args.allow_unavailable_history,
        )
    )
    print(json.dumps(record.model_dump(), indent=2, ensure_ascii=False))
    sys.exit(0 if record.ok else 1)


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

    verify = subparsers.add_parser(
        "verify-paper",
        help=(
            "Verify a paper's values and provenance in an experiment "
            "repository and build its PDF (the CI gate)"
        ),
    )
    verify.add_argument(
        "--local-path",
        default=".",
        help="Experiment repository checkout to verify (default: .)",
    )
    verify.add_argument(
        "--template",
        action="append",
        help=(
            "LaTeX template to verify (repeatable); default: every known "
            "template under .research/latex/ that has a main.tex"
        ),
    )
    verify.add_argument(
        "--output-dir",
        default="paper-artifact",
        help="Where the built PDFs go",
    )
    verify.add_argument(
        "--no-provenance",
        action="store_true",
        help="Skip the Seyval provenance cross-check entirely",
    )
    verify.add_argument(
        "--allow-unavailable-provenance",
        action="store_true",
        help=(
            "Do not fail when the provenance check cannot reach Seyval "
            "(a real mismatch still fails); CI should not pass this"
        ),
    )
    verify.add_argument(
        "--no-require-paper-values",
        action="store_true",
        help="Allow a paper that does not use the canonical-record system",
    )
    verify.add_argument(
        "--allow-unavailable-history",
        action="store_true",
        help=(
            "Do not fail when record.json's append-only git history cannot "
            "be checked (shallow clone); CI should not pass this"
        ),
    )

    record = subparsers.add_parser(
        "verify-record",
        help=(
            "Verify .research/record.json against the run outputs, its own "
            "git history and the execution platform — no paper required. "
            "Meant to be the required check on the protected branch"
        ),
    )
    record.add_argument(
        "--local-path",
        default=".",
        help="Experiment repository checkout to verify (default: .)",
    )
    record.add_argument(
        "--no-provenance",
        action="store_true",
        help="Skip the Seyval provenance cross-check entirely",
    )
    record.add_argument(
        "--allow-unavailable-provenance",
        action="store_true",
        help=(
            "Do not fail when the provenance check cannot reach Seyval "
            "(a real mismatch still fails); CI should not pass this"
        ),
    )
    record.add_argument(
        "--allow-unavailable-history",
        action="store_true",
        help=(
            "Do not fail when record.json's append-only git history cannot "
            "be checked (shallow clone); CI should not pass this"
        ),
    )

    args = parser.parse_args()

    if args.command == "dashboard":
        _run_dashboard(args.host, args.port, open_browser=not args.no_browser)
    elif args.command == "verify-paper":
        _run_verify_paper(args)
    elif args.command == "verify-record":
        _run_verify_record(args)
    else:
        # No subcommand (or `mcp`): stdio MCP server, the historical default.
        _run_mcp()


if __name__ == "__main__":
    main()
