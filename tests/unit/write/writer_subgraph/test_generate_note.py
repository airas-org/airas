import pytest
from pathlib import Path
from airas.write.writer_subgraph.nodes.generate_note import generate_note


@pytest.fixture
def state() -> dict[str, str]:
    return {
        "base_method_text": "value_for_base_method_text",
        "new_method": "value_for_new_method",
        "verification_policy": "value_for_verification_policy",
        "experiment_details": "value_for_experiment_details",
        "experiment_code": "value_for_experiment_code",
        "output_text_data": "value_for_output_text_data",
        "analysis_report": "value_for_analysis_report",
    }


def test_generate_note_without_figures(state: dict[str, str]) -> None:
    result = generate_note(state)

    expected_substrings = [
        "# Title",
        "# Methods",
        "# Codes",
        "# Results",
        "# Analysis",
        "base_method_text: value_for_base_method_text",
        "experiment_code: value_for_experiment_code",
        "No figures available.",
    ]
    for substring in expected_substrings:
        assert substring in result


def test_generate_note_with_figures(tmp_path: Path, state: dict[str, str]) -> None:
    fig1 = tmp_path / "fig1.pdf"
    fig1.write_text("dummy")
    fig2 = tmp_path / "fig2.pdf"
    fig2.write_text("dummy")

    result = generate_note(state, figures_dir=str(tmp_path))
    assert "The following figures are available" in result
    assert "- fig1.pdf" in result
    assert "- fig2.pdf" in result


@pytest.mark.parametrize(
    "missing_key",
    [
        "base_method_text",
        "new_method",
        "verification_policy",
        "experiment_details",
        "experiment_code",
        "output_text_data",
        "analysis_report",
    ],
)
def test_generate_note_missing_key(state: dict[str, str], missing_key: str) -> None:
    state.pop(missing_key)
    with pytest.raises(KeyError) as exc:
        generate_note(state)
    assert missing_key in str(exc.value)
