import pytest
from pydantic import ValidationError
from pathlib import Path
import json


from lib_prep_tools.download import DownloadListConfig, load_config, load_manifest, DownloadManifest

def test_valid_file_load_config(tmp_path: Path):
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

def test_nonexistent_file_load_config(tmp_path: Path):
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
