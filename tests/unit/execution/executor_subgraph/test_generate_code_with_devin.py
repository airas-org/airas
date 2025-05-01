import pytest
import airas.execution.executor_subgraph.nodes.generate_code_with_devin as mod


@pytest.fixture
def fake_headers() -> dict[str, str]:
    return {"Authorization": "Bearer token"}


@pytest.fixture
def fake_session_response() -> dict[str, str]:
    return {"session_id": "sess123", "url": "https://devin.ai/session/sess123"}


def test_request_create_session(
    monkeypatch: pytest.MonkeyPatch,
    fake_headers: dict[str, str],
    fake_session_response: dict[str, str],
) -> None:
    captured = {}

    def _fake_retry_request(fn, *args, **kwargs) -> dict[str, str]:
        captured["fetch_function"] = fn
        captured.update({"args": args, "kwargs": kwargs})
        return fake_session_response

    monkeypatch.setattr(mod, "retry_request", _fake_retry_request)

    repo_url = "https://github.com/owner/repo"
    branch = "my-branch"
    new_method = "do X"
    exp_code = "print('hello')"

    result = mod._request_create_session(
        headers=fake_headers,
        repository_url=repo_url,
        branch_name=branch,
        new_method=new_method,
        experiment_code=exp_code,
    )

    assert result == fake_session_response

    assert captured["fetch_function"] == mod.fetch_api_data
    assert captured["args"][0] == "https://api.devin.ai/v1/sessions"

    assert captured["kwargs"]["method"] == "POST"
    assert captured["kwargs"]["headers"] is fake_headers

    payload = captured["kwargs"]["data"]
    assert payload.get("idempotent") is True
    prompt = payload.get("prompt", "")

    assert f"## Repository URL\n{repo_url}" in prompt
    assert f"## Branch Name\n{branch}" in prompt
    assert "# New Method" in prompt and new_method in prompt
    assert "# Experiment Code" in prompt and exp_code in prompt


def test_generate_code_with_devin_success(
    monkeypatch: pytest.MonkeyPatch,
    fake_headers: dict[str, str],
    fake_session_response: dict[str, str],
) -> None:
    def _fake_request_create_session(
        headers: dict[str, str],
        repository_url: str,
        branch_name: str,
        new_method: str,
        experiment_code: str,
    ) -> dict[str, str]:
        return fake_session_response

    monkeypatch.setattr(mod, "_request_create_session", _fake_request_create_session)

    sid, url = mod.generate_code_with_devin(
        headers=fake_headers,
        github_owner="owner",
        repository_name="repo",
        branch_name="branch",
        new_method="NM",
        experiment_code="EC",
    )
    assert sid == fake_session_response["session_id"]
    assert url == fake_session_response["url"]


def test_generate_code_with_devin_failure(
    monkeypatch: pytest.MonkeyPatch, fake_headers: dict[str, str]
) -> None:
    monkeypatch.setattr(mod, "_request_create_session", lambda *args, **kwargs: None)

    sid, url = mod.generate_code_with_devin(
        headers=fake_headers,
        github_owner="owner",
        repository_name="repo",
        branch_name="branch",
        new_method="NM",
        experiment_code="EC",
    )
    assert sid is None and url is None
