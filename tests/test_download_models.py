import pytest
from pydantic import ValidationError
from lib_prep_tools.download import CompendiaDownloadConfig, DownloadListConfig, ManifestFileStatusEntry, DownloadManifest

"""
Unit tests for pydantic models in lib_prep_tools.download
"""

def test_valid_compendia_download_config():
    valid_config = {
        "compendia_id": "compendia_1",
        "expression_url": "http://example.com/expression",
        "metadata_url": "http://example.com/metadata"
    }
    config = CompendiaDownloadConfig(**valid_config)
    assert config.compendia_id == "compendia_1"
    assert str(config.expression_url) == "http://example.com/expression"
    assert str(config.metadata_url) == "http://example.com/metadata"


@pytest.mark.parametrize("invalid_config", [
{
        "compendia_id": "compendia/1",  # Invalid character '/'
        "expression_url": "http://example.com/expression",
        "metadata_url": "http://example.com/metadata"
    },
    {
        "compendia_id": "compendia*1",  # Invalid character '*'
        "expression_url": "http://example.com/expression",
        "metadata_url": "http://example.com/metadata"
    },
    {
        "compendia_id": "compendia?1",  # Invalid character '?'
        "expression_url": "http://example.com/expression",
        "metadata_url": "http://example.com/metadata"
    },
    {
        "compendia_id": "compendia<1",  # Invalid character '<'
        "expression_url": "http://example.com/expression",
        "metadata_url": "http://example.com/metadata"
    },
    {
        "compendia_id": "compendia>1",  # Invalid character '   >'
        "expression_url": "http://example.com/expression",
        "metadata_url": "http://example.com/metadata"
    },
    {
        "compendia_id": "compendia 1",  # Invalid character ' '
        "expression_url": "http://example.com/expression",
        "metadata_url": "http://example.com/metadata"
    }
])
def test_invalid_compendia_id_in_config(invalid_config):
    with pytest.raises(ValidationError):
        CompendiaDownloadConfig(**invalid_config)


def test_invalid_expression_url_in_config():
    invalid_config = {
        "compendia_id": "compendia_1",
        "expression_url": "not_a_url",  # Invalid URL
        "metadata_url": "http://example.com/metadata"
    }
    with pytest.raises(ValidationError):
        CompendiaDownloadConfig(**invalid_config)


def test_invalid_metadata_url_in_config():
    invalid_config = {
        "compendia_id": "compendia_1",
        "expression_url": "http://example.com/expression",
        "metadata_url": "not_a_url"  # Invalid URL
    }
    with pytest.raises(ValidationError):
        CompendiaDownloadConfig(**invalid_config)


def test_valid_download_list_config():
    valid_config = [
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
    config = DownloadListConfig(root=valid_config)
    assert len(config.root) == 2
    for compendia_download_config in config.root:
        assert isinstance(compendia_download_config, CompendiaDownloadConfig)


def test_invalid_compendia_in_download_list_config():
    invalid_config = [      
        {
            "compendia_id": "compendia_1",
            "expression_url": "http://example.com/expression1",
            "metadata_url": "http://example.com/metadata1"
        },
        {
            "compendia_id": "compendia/2",  # Invalid compendia_id
            "expression_url": "http://example.com/expression2",
            "metadata_url": "http://example.com/metadata2"
        }
    ]
    with pytest.raises(ValidationError):
        DownloadListConfig(invalid_config)


def test_invalid_download_list_in_download_list_config():
    invalid_config = {
        "compendia_downloads": "not_a_list"  # Invalid type
    }
    with pytest.raises(ValidationError):
        DownloadListConfig(**invalid_config)


valid_dataset_model_entry = {
    "last_download": "2023-10-01T12:00:00",
    "md5checksum": "d41d8cd98f00b204e9800998ecf8427e",
    "file_size": 123456,
    "status": "completed",
    "software_version": "1.0.0"
}


def test_valid_dataset_entry_model():
    entry = ManifestFileStatusEntry(**valid_dataset_model_entry)


def test_invalid_datetime_dataset_entry_model():
    invalid_entry = valid_dataset_model_entry.copy()
    invalid_entry["last_download"] = "not_a_datetime"  # Invalid datetime
    with pytest.raises(ValidationError):
        ManifestFileStatusEntry(**invalid_entry)


def test_invalid_md5checksum_dataset_entry_model():
    invalid_entry = valid_dataset_model_entry.copy()
    invalid_entry["md5checksum"] = 123456  # Invalid type
    with pytest.raises(ValidationError):
        ManifestFileStatusEntry(**invalid_entry)


def test_invalid_file_size_dataset_entry_model():
    invalid_entry = valid_dataset_model_entry.copy()
    invalid_entry["file_size"] = "123456b"  # Invalid type
    with pytest.raises(ValidationError):
        ManifestFileStatusEntry(**invalid_entry)


def test_invalid_status_dataset_entry_model():
    invalid_entry = valid_dataset_model_entry.copy()
    invalid_entry["status"] = 100  # Invalid type
    with pytest.raises(ValidationError):
        ManifestFileStatusEntry(**invalid_entry)


def test_invalid_software_version_dataset_entry_model():
    invalid_entry = valid_dataset_model_entry.copy()
    invalid_entry["software_version"] = 1.0  # Invalid type
    with pytest.raises(ValidationError):
        ManifestFileStatusEntry(**invalid_entry)