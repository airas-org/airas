from pathlib import Path
from typing import Any

from airas.usecases.verification.ci_gate import detect_templates, gate_failures


def _merged(
    ok: bool = True,
    configured: bool = True,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "paper_values_configured": configured,
        "paper_values": {"provenance": provenance, "unverified": []},
    }


# --------------------------------------------------
# detect_templates
# --------------------------------------------------


def test_detects_only_written_known_templates(tmp_path: Path) -> None:
    latex = tmp_path / ".research" / "latex"
    (latex / "mdpi").mkdir(parents=True)
    (latex / "mdpi" / "main.tex").write_text("x")
    (latex / "iclr2024").mkdir()  # template present but no paper written
    (latex / "homebrew").mkdir()  # unknown template directory
    (latex / "homebrew" / "main.tex").write_text("x")

    assert detect_templates(str(tmp_path)) == ["mdpi"]


def test_detects_nothing_without_latex_dir(tmp_path: Path) -> None:
    assert detect_templates(str(tmp_path)) == []


# --------------------------------------------------
# gate_failures — the CI policy on top of the merged report
# --------------------------------------------------


def test_passes_when_verified(tmp_path: Path) -> None:
    merged = _merged(provenance={"status": "verified", "detail": ""})
    assert gate_failures(merged, True, True) == []


def test_fails_on_not_ok() -> None:
    merged = _merged(ok=False, provenance={"status": "verified", "detail": ""})
    assert any("ok=false" in f for f in gate_failures(merged, True, True))


def test_fails_when_paper_values_not_configured() -> None:
    merged = _merged(configured=False)
    merged["paper_values"] = {"provenance": None, "unverified": []}
    assert any("values.json" in f for f in gate_failures(merged, True, True))
    # ... unless the caller opted out.
    assert gate_failures(merged, False, True) == []


def test_unavailable_provenance_fails_the_gate() -> None:
    # Locally "unavailable" only warns; the gate must not shrug it off.
    merged = _merged(provenance={"status": "unavailable", "detail": "no key"})
    failures = gate_failures(merged, True, True)
    assert any("unavailable" in f for f in failures)
    assert gate_failures(merged, True, False) == []


def test_missing_provenance_check_fails_the_gate() -> None:
    merged = _merged(provenance=None)
    assert any("did not run" in f for f in gate_failures(merged, True, True))


def test_provenance_not_required_for_unconfigured_paper() -> None:
    # No values.json -> there is nothing to cross-check; the missing
    # configuration itself is the (single) failure.
    merged = _merged(configured=False, provenance=None)
    failures = gate_failures(merged, True, True)
    assert len(failures) == 1
    assert "values.json" in failures[0]
