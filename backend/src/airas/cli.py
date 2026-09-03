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


def _run_verify_paper(args: "argparse.Namespace") -> None:
    import asyncio
    import sys

    from airas.usecases.verification.ci_gate import (
        REPORT_FILENAME,
        detect_templates,
        run_paper_gate,
    )

    templates = args.template or detect_templates(args.local_path)
    if not templates:
        print(
            "No paper found: no known template under .research/latex/ has a main.tex",
            file=sys.stderr,
        )
        sys.exit(2)

    summary = asyncio.run(
        run_paper_gate(
            local_repo_path=args.local_path,
            templates=templates,
            output_dir=args.output_dir,
            check_provenance=not args.no_provenance,
            require_paper_values=not args.no_require_paper_values,
            require_provenance=not (
                args.no_provenance or args.allow_unavailable_provenance
            ),
            require_history=not args.allow_unavailable_history,
        )
    )

    for result in summary["templates"]:
        status = "PASS" if result["ok"] else "FAIL"
        print(f"[{status}] {result['template']}")
        for failure in result["failures"]:
            print(f"  - {failure}")
        for claim in result["unverified"]:
            print(f"  ! \\unverified for human review: {claim}")
        for claim_id in result["unverified_claims"]:
            print(f"  ! unverified claim: {claim_id} (no verified run backs it yet)")
        if result["pdf"]:
            print(f"  pdf: {result['pdf']}")
    print(f"Full report: {args.output_dir}/{REPORT_FILENAME}")

    sys.exit(0 if summary["ok"] else 1)


def _run_verify_record(args: "argparse.Namespace") -> None:
    import asyncio
    import sys

    from airas.usecases.verification.ci_gate import (
        RECORD_REPORT_FILENAME,
        run_record_gate,
    )

    summary = asyncio.run(
        run_record_gate(
            local_repo_path=args.local_path,
            output_dir=args.output_dir,
            check_provenance=not args.no_provenance,
            require_provenance=not (
                args.no_provenance or args.allow_unavailable_provenance
            ),
            require_history=not args.allow_unavailable_history,
        )
    )

    papers = ", ".join(summary["papers"]) if summary["papers"] else "no paper"
    print(
        f"[{'PASS' if summary['ok'] else 'FAIL'}] record ({summary['stage']}; {papers})"
    )
    for failure in summary["failures"]:
        print(f"  - {failure}")
    for result in summary["results"]:
        for claim in result["unverified"]:
            print(f"  ! \\unverified for human review: {claim}")
    for claim_id in summary["unverified_claims"]:
        print(f"  ! unverified claim: {claim_id} (no verified run backs it yet)")
    print(f"Full report: {args.output_dir}/{RECORD_REPORT_FILENAME}")

    sys.exit(0 if summary["ok"] else 1)


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
        help="Where the PDFs and verification-report.json go",
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
        "--output-dir",
        default="record-artifact",
        help="Where record-verification-report.json goes",
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
