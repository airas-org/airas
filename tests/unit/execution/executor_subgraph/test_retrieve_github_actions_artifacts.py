import pytest
import io
import zipfile

import airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts as mod


@pytest.fixture
def zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('output.txt', 'OUT')
        z.writestr('error.txt', 'ERR')
        z.writestr('doc.pdf', b'%PDF')
    return buf.getvalue()


@pytest.fixture
def dummy_client(zip_bytes):
    class DummyClient:
        def __init__(self):
            self.infos = {"artifacts":[{"name":"artifact","id":1,"workflow_run":{"id":"run"}}]}
            self.downloaded = []
        def list_repository_artifacts(self, github_owner, repository_name):
            return self.infos
        def download_artifact_archive(self, github_owner, repository_name, aid):
            self.downloaded.append(aid)
            return zip_bytes
    return DummyClient()


@pytest.mark.parametrize("infos, run_id", [
    (None, "run"),
    ({}, "run"),
    ({"artifacts": []}, "run"),
])
def test_retrieve_errors(tmp_path, infos, run_id):
    class C:
        def list_repository_artifacts(self, *args, **kwargs): return infos
        def download_artifact_archive(self, *args, **kwargs): pytest.skip()
    with pytest.raises(RuntimeError):
        mod.retrieve_github_actions_artifacts("o","r", run_id, str(tmp_path), 0, client=C())


@pytest.mark.parametrize("infos, target, expected", [
    ({"artifacts":[{"name":"a","id":10,"workflow_run":{"id":"x"}}]}, "x", {"a":10}),
    ({"artifacts":[]}, "x", {}),
])
def test_parse_artifacts_id(infos, target, expected):
    assert mod._parse_artifacts_id(infos, target) == expected


def test_save_and_copy(tmp_path, zip_bytes):
    save_dir = tmp_path / "iter"
    save_dir.mkdir()
    mod._save_zip_and_extract(zip_bytes, str(save_dir), "artifact")
    assert (save_dir/"output.txt").read_text() == "OUT"
    assert not (save_dir/"artifact.zip").exists()

    pdf = save_dir/"test.pdf"
    pdf.write_bytes(b'%PDF')
    dest = tmp_path/"images"
    mod._copy_images_to_latest_dir(str(save_dir), str(dest))
    assert (dest/"test.pdf").exists()


def test_retrieve_success(tmp_path, dummy_client):
    out, err = mod.retrieve_github_actions_artifacts(
        "owner","repo","run", str(tmp_path), fix_iteration_count=1,
        client=dummy_client
    )
    assert out == "OUT" and err == "ERR"
    assert dummy_client.downloaded == [1]
    iter_dir = tmp_path / 'iteration_1'
    assert not (iter_dir / 'artifact.zip').exists()
    imgs = list((tmp_path / 'images').glob('*.pdf'))
    assert imgs and imgs[0].name == 'doc.pdf'
