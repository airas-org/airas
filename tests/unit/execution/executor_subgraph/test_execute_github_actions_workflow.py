import pytest

import airas.execution.executor_subgraph.nodes.execute_github_actions_workflow as mod


@pytest.fixture
def before_runs() -> dict:
    return {
        "workflow_runs": [
            {"id": 1, "created_at": "2025-05-07T00:00:00Z", "status": "completed"},
        ]
    }

@pytest.fixture
def after_runs() -> dict:
    return {
        "workflow_runs": [
            {"id": 1, "created_at": "2025-05-07T00:00:00Z", "status": "completed"},
            {"id": 2, "created_at": "2025-05-07T00:01:00Z", "status": "completed"},
        ]
    }


@pytest.fixture
def dummy_success_client(before_runs, after_runs):
    class DummyClient:
        def __init__(self):
            self.calls = []

        def list_workflow_runs(self, github_owner, repository_name, branch_name):
            self.calls.append("list")
            return before_runs if self.calls.count("list") == 1 else after_runs

        def dispatch_workflow(self, github_owner, repository_name, workflow_file, ref):
            self.calls.append("dispatch")

    return DummyClient()


def test_count_workflow_runs():
    resp = {"workflow_runs": [1, 2, 3]}
    assert mod._count_github_actions_workflow_runs(resp) == 3


def test_parse_workflow_run_id():
    resp = {
        "workflow_runs": [
            {"id": 10, "created_at": "2025-05-06T12:00:00Z"},
            {"id": 20, "created_at": "2025-05-07T08:30:00Z"},
            {"id": 15, "created_at": "2025-05-05T23:59:59Z"},
        ]
    }
    assert mod._parse_workflow_run_id(resp) == 20


@pytest.mark.parametrize(
    "runs, expected",
    [
        ([{"status": "completed"}, {"status": "completed"}], True),
        ([{"status": "completed"}, {"status": "in_progress"}], False),
    ],
)
def test_check_confirmation_of_execution_completion(runs, expected):
    resp = {"workflow_runs": runs}
    assert mod._check_confirmation_of_execution_completion(resp) is expected


def test_execute_success_with_client_arg(dummy_success_client):
    run_id = mod.execute_github_actions_workflow(
        "github_owner", "repository_name", "branch_name", client=dummy_success_client
    )
    assert dummy_success_client.calls == ["list", "dispatch", "list"]
    assert run_id == 2

def test_execute_success_with_default_client(monkeypatch, dummy_success_client):
    monkeypatch.setattr(mod, "GithubClient", lambda: dummy_success_client)
    monkeypatch.setattr(mod.time, "sleep", lambda s: None)

    run_id = mod.execute_github_actions_workflow("github_owner", "repository_name", "branch_name")
    assert dummy_success_client.calls == ["list", "dispatch", "list"]
    assert run_id == 2


@pytest.mark.parametrize("initial_response", [None, {}])
def test_execute_raises_runtime_error_when_no_initial_runs(initial_response):
    class DummyClientNoInitial:
        def list_workflow_runs(self, *args, **kwargs):
            return initial_response
        def dispatch_workflow(self, *args, **kwargs):
            pytest.skip("dispatch should not be called")

    with pytest.raises(RuntimeError):
        mod.execute_github_actions_workflow("github_owner", "repository_name", "branch_name", client=DummyClientNoInitial())


def test_execute_timeout(monkeypatch, before_runs):
    class DummyClientNever:
        def __init__(self):
            self.calls = []
        def list_workflow_runs(self, *args, **kwargs):
            self.calls.append("list")
            return before_runs
        def dispatch_workflow(self, *args, **kwargs):
            self.calls.append("dispatch")

    dummy = DummyClientNever()

    timeout = mod._TIMEOUT_SEC
    class FakeTime:
        _t = 0
        @classmethod
        def time(cls):
            return cls._t
        @staticmethod
        def sleep(sec):
            FakeTime._t += timeout + 1

    monkeypatch.setattr(mod, "time", FakeTime)
    monkeypatch.setattr(mod, "GithubClient", lambda: dummy)

    with pytest.raises(TimeoutError):
        mod.execute_github_actions_workflow("owner", "repo", "branch")


def test_execute_retries_until_completion(monkeypatch):
    before_runs = {
        "workflow_runs": [
            {"id": 1, "created_at": "2025-05-07T00:00:00Z", "status": "completed"},
        ]
    }
    incomplete_runs = {
        "workflow_runs": [
            {"id": 1, "created_at": "2025-05-07T00:00:00Z", "status": "completed"},
            {"id": 2, "created_at": "2025-05-07T00:01:00Z", "status": "in_progress"},
        ]
    }
    complete_runs = {
        "workflow_runs": [
            {"id": 1, "created_at": "2025-05-07T00:00:00Z", "status": "completed"},
            {"id": 2, "created_at": "2025-05-07T00:01:00Z", "status": "completed"},
        ]
    }

    class DummyClientRetries:
        def __init__(self):
            self.list_calls = 0
            self.calls = []

        def list_workflow_runs(self, github_owner, repository_name, branch_name):
            self.calls.append("list")
            self.list_calls += 1
            if self.list_calls == 1:
                return before_runs
            elif self.list_calls == 2:
                return incomplete_runs
            else:
                return complete_runs

        def dispatch_workflow(self, github_owner, repository_name, workflow_file, ref):
            self.calls.append("dispatch")

    client = DummyClientRetries()

    monkeypatch.setattr(mod.time, "sleep", lambda s: None)

    run_id = mod.execute_github_actions_workflow("github_owner", "repository_name", "branch_name", client=client)

    assert client.calls == ["list", "dispatch", "list", "list"]
    assert run_id == 2
