from pydantic import BaseModel, HttpUrl, field_validator
from typing import List
from pathlib import Path
import re
import json


class CompendiaDownloadConfig(BaseModel):
    compendia_id: str
    expression_url: HttpUrl
    metadata_url: HttpUrl

    @field_validator('compendia_id')
    @classmethod
    def directory_name_safe(cls, v: str) -> str:
        # Only allow alphanumeric, dash, underscore, and dot. Underscore is considered alphanumeric (\w) here. + means one or more, $ means go until the end of the string.
        if not re.match(r'^[\w\-.]+$', v):
            raise ValueError('compendia_id must be directory name safe (alphanumeric, dash, underscore, dot)')
        return v


class DownloadListConfig(BaseModel):
    compendia_downloads: List[CompendiaDownloadConfig]


def load_config(file_path: Path) -> DownloadListConfig:
    """
    Load a json config file and parse it into a DownloadListConfig object.
    """
    # Check that the file path exists
    if not file_path.exists():
        raise FileNotFoundError(f"Config file {file_path} does not exist.")
    with open(file_path, 'r') as f:
        config_data = json.load(f)
    return DownloadListConfig(**config_data)