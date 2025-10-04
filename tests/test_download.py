import pytest
from pydantic import ValidationError
from pathlib import Path
import json
import requests

from lib_prep_tools.download import DownloadListConfig, load_config, load_manifest, DownloadManifest, download_file, need_download, STATUS_SUCCESS, STATUS_FAILED

"""
Unit tests for functions in lib_prep_tools.download
"""

def test_load_config_valid_file(tmp_path: Path):
    config_data = [
        {
            "compendia_id": "compendia_1",
            "expression_url": "http://example.com/expression1",
            "metadata_url": "http://example.com/metadata1"
        },
        {
            "compendia_id": "compendia_2",
            "expression_url": "http://example.com/expression2",
            "metadata_url": "http://example.com/metadata2"
        }
    ]
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        import json
        json.dump(config_data, f)
    config = load_config(config_file)
    assert isinstance(config, DownloadListConfig)

def test_load_config_nonexistent_file(tmp_path: Path):
    non_existent_file = tmp_path / "non_existent_config.json"
    with pytest.raises(FileNotFoundError):
        load_config(non_existent_file)

def test_load_manifest_initialize_new_manifest(tmp_path: Path):
    empty_download_manifest = load_manifest(tmp_path / "non_existent_manifest.json")
    assert isinstance(empty_download_manifest, DownloadManifest)
    assert len(empty_download_manifest.root) == 0

def test_load_manifest_with_existing_file(tmp_path: Path):
    valid_dataset_model_entry = {
        "last_download": "2023-10-01T12:00:00",
        "md5checksum": "d41d8cd98f00b204e9800998ecf8427e",
        "file_size": 123456,
        "status": "completed",
        "software_version": "1.0.0"
    }
    
    manifest_data = {
        "dataset_1": valid_dataset_model_entry.copy(),
        "dataset_2": valid_dataset_model_entry.copy()
    }
    manifest_file = tmp_path / "manifest.json"
    with open(manifest_file, 'w') as f:
        import json
        json.dump(manifest_data, f)
    manifest = load_manifest(manifest_file)
    assert isinstance(manifest, DownloadManifest)
    assert len(manifest.root) == 2


def test_download_file_valid_url(tmp_path: Path, requests_mock):
    mock_url = "http://table.com/file"
    target_path = tmp_path / "downloaded_file.txt"
    requests_mock.get(mock_url, content=b"expression table content")
    result_path = download_file(mock_url, target_path)
    assert result_path == target_path
    assert target_path.exists()
    assert target_path.stat().st_size > 0 # file is not empty. st_size retrieves file size in bytes


def test_download_file_invalid_url(tmp_path: Path, requests_mock):
    mock_url = "http://table.com/file"
    target_path = tmp_path / "downloaded_file.txt"
    requests_mock.get(mock_url, status_code=404)
    result_path = download_file(mock_url, target_path)
    assert result_path == None
    assert not target_path.exists()

need_download_manifest = DownloadManifest(root={
        "compendia_1": {
            "last_download": "2000-01-01T12:00:00",
            "md5checksum": "d41d8cd98f00b204e9800998ecf8427e",
            "file_size": 123456,
            "status": STATUS_SUCCESS,
            "software_version": "0.0.0"
        }
    })

def test_need_download_compendia_missing():
    assert need_download(need_download_manifest, "compendia_2", "0.0.0") == True

def test_need_download_status_not_success():
    need_download_manifest.root["compendia_1"].status = STATUS_FAILED
    assert need_download(need_download_manifest, "compendia_1", "0.0.0") == True
    need_download_manifest.root["compendia_1"].status = STATUS_SUCCESS

def test_need_download_software_version_mismatch():
    assert need_download(need_download_manifest, "compendia_1", "0.0.1") == True

def test_need_download_no_download_needed():
    assert need_download(need_download_manifest, "compendia_1", "0.0.0") == False

