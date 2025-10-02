import pytest
from pydantic import ValidationError

from lib_prep_tools.download import CompendiaDownloadConfig, DownloadListConfig

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

def test_valid_download_config():
    valid_config = {
        "compendia_downloads": [
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
    }
    config = DownloadListConfig(**valid_config)
    assert len(config.compendia_downloads) == 2
    for compendia_download_config in config.compendia_downloads:
        assert isinstance(compendia_download_config, CompendiaDownloadConfig)

def test_invalid_compendia_in_download_list_config():
    invalid_config = {
        "compendia_downloads": [
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
    }
    with pytest.raises(ValidationError):
        DownloadListConfig(**invalid_config)

def test_invalid_download_list_in_download_list_config():
    invalid_config = {
        "compendia_downloads": "not_a_list"  # Invalid type
    }
    with pytest.raises(ValidationError):
        DownloadListConfig(**invalid_config)