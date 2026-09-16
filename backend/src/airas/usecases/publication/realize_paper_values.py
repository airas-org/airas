"""Realizing the record from run outputs and rendering the paper values."""

import asyncio
from pathlib import Path
from typing import Any

from airas.core.research_paths import RECORD_PATH
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.infra.local_git import (
    normalize_git_url,
    remote_origin_url,
)
from airas.research_record.derive_results import (
    update_record_with_results,
)
from airas.research_record.read_run_outputs import (
    load_metrics_data,
    load_provenance_manifest,
)
from airas.research_record.store import (
    commit_record_paths,
    load_record,
    record_path,
    save_record,
)
from airas.usecases.publication.map_record_to_publication import (
    TABLES_DIR_NAME,
    VALUES_TEX_FILENAME,
    record_link_commit,
    render_table_tex,
    render_values_tex,
    resolve_paper_values,
)
from airas.usecases.publication.verify_paper import (
    scan_main_tex,
)
from airas.usecases.publication.write_tex_files import (
    write_claims_tex,
)


async def realize_paper_values(
    local_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
) -> dict[str, Any]:
    """Append each run's outputs to the record and render values.tex."""

    def _run() -> dict[str, Any]:
        record = load_record(local_path)
        try:
            metrics_data = load_metrics_data(local_path)
        except ValueError:
            # A record verified by lean or llm_judge alone has no metrics.
            metrics_data = {}
        root = Path(local_path).expanduser().resolve()
        manifest = load_provenance_manifest(root)

        # Results are facts, so they are appended rather than replaced:
        # running the same configuration again adds an entry and the earlier
        # numbers stay, which is what makes the record a lab notebook as well
        # as a verification input.
        statuses, appended = update_record_with_results(
            root, record, metrics_data, manifest
        )

        save_record(local_path, record)
        # Two commits on purpose: the link in values.tex must name the commit
        # that holds the record it links into, and that sha does not exist
        # until record.json is committed. record.json is untouched by the
        # second commit, so "the commit that last wrote record.json" stays a
        # deterministic answer for the verifier.
        commit_record_paths(local_path, [RECORD_PATH], "record: realize results")
        # commit_paths answers HEAD when record.json did not change (a second
        # update_record after a paper edit), and HEAD is then not the record's
        # commit. Ask git the same question the verifier asks.
        record_commit = record_link_commit(root)

        latex_dir = root / ".research" / "latex" / latex_template_name
        latex_dir.mkdir(parents=True, exist_ok=True)
        main_tex = latex_dir / "main.tex"
        used_keys = (
            scan_main_tex(main_tex.read_text(encoding="utf-8"))[1]
            if main_tex.is_file()
            else []
        )
        paper_values, _ = resolve_paper_values(record, metrics_data, used_keys)

        remote = remote_origin_url(root)
        values_tex_path = latex_dir / VALUES_TEX_FILENAME
        values_tex_path.write_text(
            render_values_tex(
                paper_values,
                normalize_git_url(remote) if remote else None,
                record_commit,
            ),
            encoding="utf-8",
        )
        tables: dict[str, str] = {}
        table_specs = record.active_tables()
        if table_specs:
            tables_dir = latex_dir / TABLES_DIR_NAME
            tables_dir.mkdir(parents=True, exist_ok=True)
            for spec in table_specs:
                table_path = tables_dir / f"{spec.key}.tex"
                table_path.write_text(
                    render_table_tex(spec, metrics_data), encoding="utf-8"
                )
                tables[spec.key] = str(table_path)
        claims_tex = write_claims_tex(local_path, latex_template_name, record)
        commit_targets = [
            f".research/latex/{latex_template_name}/{VALUES_TEX_FILENAME}",
            claims_tex,
        ]
        # tables/ exists only once a table has been declared, and git add is
        # fatal on a pathspec that matches nothing.
        if tables:
            commit_targets.append(
                f".research/latex/{latex_template_name}/{TABLES_DIR_NAME}"
            )
        commit = commit_record_paths(
            local_path, commit_targets, "record: render paper values"
        )
        return {
            "values": {v.ref: v.display for v in paper_values},
            "claims": {
                s.id: {"verified": s.verified, "verdict": s.verdict} for s in statuses
            },
            "results_appended": appended,
            "record_commit": record_commit,
            "tables": tables,
            "record_path": str(record_path(local_path)),
            "values_tex_path": str(values_tex_path),
            "claims_tex_path": claims_tex,
            "commit": commit,
        }

    result = await asyncio.to_thread(_run)
    result["usage"] = (
        "\\input{values.tex} in the preamble, \\input{tables/<key>.tex} where "
        "each table belongs, \\input{claims.tex} where the claims are listed, "
        "then \\airasval{<key>} wherever the paper states a number; the "
        "realized files are already committed — push to the staging ref and "
        "let CI decide whether it may reach the protected branch"
    )
    return result
