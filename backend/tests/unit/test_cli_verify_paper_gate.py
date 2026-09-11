import argparse

import pytest

from airas import cli


def test_paper_gate_passes_when_there_is_no_paper(tmp_path):
    args = argparse.Namespace(
        local_path=str(tmp_path),
        template=None,
        no_provenance=False,
        allow_unavailable_provenance=False,
        no_require_paper_values=False,
        allow_unavailable_history=False,
    )
    with pytest.raises(SystemExit) as exit:
        cli._run_verify_paper(args)
    assert exit.value.code == 0


def test_publish_is_a_noop_when_there_is_no_paper(tmp_path):
    args = argparse.Namespace(
        local_path=str(tmp_path),
        template=None,
        output_dir=str(tmp_path / "out"),
    )
    with pytest.raises(SystemExit) as exit:
        cli._run_publish_paper(args)
    assert exit.value.code == 0
