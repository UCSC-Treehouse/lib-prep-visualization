import pytest
from pathlib import Path
from datetime import datetime

from lib_prep_tools.download import (
    DownloadListConfig, 
    DownloadManifest, 
    ManifestFileStatusEntry, 
    ManifestCompendiaEntry, 
    load_config, 
    load_manifest, 
    download_file, 
    file_status_need_download,
    get_or_create_manifest_entry, 
    download_file_with_manifest_update, 
    STATUS_SUCCESS,
    STATUS_FAILED
)

"""
Unit tests for functions in lib_prep_tools.download
"""

manifest_file_status_entry = ManifestFileStatusEntry(
    last_download="2000-01-01T12:00:00",
    md5checksum="d41d8cd98f00b204e9800998ecf8427e",
    file_size=123456,
    status="completed",
    software_version="1.0.0"
)

manifest_compendia_entry = ManifestCompendiaEntry(
    expression=manifest_file_status_entry,
    metadata=manifest_file_status_entry
)

download_manifest = DownloadManifest({
    "compendia_1": manifest_compendia_entry,
    "compendia_2": manifest_compendia_entry
})

need_download_manifest_file_status_entry = ManifestFileStatusEntry(
    last_download="2020-01-01T12:00:00",
    md5checksum="d41d8cd98f00b204e9800998ecf8427e",
    file_size=123456,
    status=STATUS_SUCCESS,
    software_version="0.0.0"
)



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

def test_load_manifest_valid_file(tmp_path: Path):
    manifest_file = tmp_path / "manifest.json"
    with open(manifest_file, 'w') as f:
        f.write(download_manifest.model_dump_json(indent=4))
    manifest = load_manifest(manifest_file)
    assert isinstance(manifest, DownloadManifest)
    assert len(manifest.root) == 2

def test_load_manifest_invalid_manifest_file_returns_new_manifest(tmp_path: Path):
    invalid_manifest_json = {
        "compendia_1": "invalid_entry"
    }
    manifest_file = tmp_path / "invalid_manifest.json"
    with open(manifest_file, 'w') as f:
        import json
        json.dump(invalid_manifest_json, f)
    manifest = load_manifest(manifest_file)
    assert isinstance(manifest, DownloadManifest)
    assert len(manifest.root) == 0  # Invalid manifest should result in empty manifest


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

def test_need_download_status_not_success():
    need_download_manifest_file_status_entry.status = STATUS_FAILED
    assert file_status_need_download(need_download_manifest_file_status_entry, "0.0.0") == True
    need_download_manifest_file_status_entry.status = STATUS_SUCCESS

def test_need_download_software_version_mismatch():
    assert file_status_need_download(need_download_manifest_file_status_entry, "0.0.1") == True

def test_need_download_no_download_needed():
    assert file_status_need_download(need_download_manifest_file_status_entry, "0.0.0") == False

def test_get_or_create_manifest_entry_existing():
    entry = get_or_create_manifest_entry(download_manifest, "compendia_1")
    assert isinstance(entry, ManifestCompendiaEntry)
    assert entry == manifest_compendia_entry

def test_get_or_create_manifest_entry_not_existing():
    entry = get_or_create_manifest_entry(download_manifest, "compendia_3")
    assert isinstance(entry, ManifestCompendiaEntry)
    assert entry != manifest_compendia_entry

def test_download_file_with_manifest_update__download_success(monkeypatch):
    target_path = Path("downloaded_file.txt")
    # download_file returning a path means successful download
    monkeypatch.setattr('lib_prep_tools.download.download_file', lambda url, target_path: target_path)
    manifest_file_status_entry = ManifestFileStatusEntry()
    # Save the "last_download" time before calling the func. This should be updated by the function if the download is successfull.
    manifest_before_time = manifest_file_status_entry.last_download
    download_file_with_manifest_update("http://example.com/file", target_path, manifest_file_status_entry, "1.0.0")
    assert manifest_file_status_entry.status == STATUS_SUCCESS
    assert manifest_file_status_entry.software_version == "1.0.0"
    assert manifest_file_status_entry.last_download != None
    assert manifest_file_status_entry.last_download != manifest_before_time

def test_download_file_with_manifest_update_download_failure(monkeypatch):
    target_path = Path("downloaded_file.txt")
    # download_file returning None means failed download
    monkeypatch.setattr('lib_prep_tools.download.download_file', lambda url, target_path: None)
    manifest_file_status_entry = ManifestFileStatusEntry(last_download=datetime.min, status=STATUS_SUCCESS, software_version="0.0.0")
    download_file_with_manifest_update("http://example.com/file", target_path, manifest_file_status_entry, "1.0.0")
    # Failed status should switch the status to failed, should not update the version, and should not change the last_download time
    assert manifest_file_status_entry.status == STATUS_FAILED
    assert manifest_file_status_entry.software_version == "0.0.0"
    assert manifest_file_status_entry.last_download == datetime.min