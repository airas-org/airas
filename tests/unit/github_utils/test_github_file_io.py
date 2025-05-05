import json
from unittest.mock import patch

import pytest

from airas.utils.github_utils.github_file_io import download_from_github


# 正常な JSON (dict) を返すケース
@patch("airas.utils.github_utils.github_file_io._download_file_bytes_from_github")
def test_download_from_github_valid_json(mock_download):
    # 辞書型データをJSON文字列に変換して、バイト列にエンコードする
    expected_data = {"key": "value"}
    json_bytes = json.dumps(expected_data).encode("utf-8")
    mock_download.return_value = json_bytes

    result = download_from_github("owner", "repo", "branch", "path/to/file")
    assert result == expected_data, "有効な JSON 辞書が復元されるべき"


# JSON 形式だが dict ではなく list のケース
@patch("airas.utils.github_utils.github_file_io._download_file_bytes_from_github")
def test_download_from_github_non_dict_json(mock_download):
    non_dict_data = ["item1", "item2"]
    json_bytes = json.dumps(non_dict_data).encode("utf-8")
    mock_download.return_value = json_bytes

    with pytest.raises(ValueError) as excinfo:
        download_from_github("owner", "repo", "branch", "path/to/file")
    assert "Decoded input is not a dictionary" in str(excinfo.value)


# JSON としてパースできない文字列の場合
@patch("airas.utils.github_utils.github_file_io._download_file_bytes_from_github")
def test_download_from_github_invalid_json(mock_download):
    # JSON ではない文字列をバイト列として返す
    mock_download.return_value = b"not a valid json"

    with pytest.raises(Exception) as excinfo:
        download_from_github("owner", "repo", "branch", "path/to/file")
    assert "Failed to parse full-state JSON" in str(excinfo.value)


# ファイルが見つからなかった場合 (None を返す)
@patch("airas.utils.github_utils.github_file_io._download_file_bytes_from_github")
def test_download_from_github_file_not_found(mock_download):
    mock_download.return_value = None

    with pytest.raises(FileNotFoundError) as excinfo:
        download_from_github("owner", "repo", "branch", "path/to/file")
    assert "Required GitHub input not found" in str(excinfo.value)
