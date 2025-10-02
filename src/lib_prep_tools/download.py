from pydantic import BaseModel, HttpUrl, field_validator, RootModel
from typing import List, Dict
from pathlib import Path
from datetime import datetime
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


class DatasetEntry(BaseModel):
    last_download: datetime
    md5checksum: str
    file_size: int
    status: str
    software_version: str

    model_config = {
        "validate_assignment": True  # validates any field change
    }

class DownloadManifest(RootModel):
    root: Dict[str, DatasetEntry]

    def add_entry(self, name: str, entry: DatasetEntry):
        """Add a new DatasetEntry under the given name."""
        if not isinstance(entry, DatasetEntry):
            raise TypeError("entry must be a DatasetEntry instance")
        self.root[name] = entry

    def get_entry(self, name: str) -> DatasetEntry:
        """Retrieve an existing DatasetEntry for modification."""
        return self.root[name]


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


def load_manifest(file_path: Path) -> DownloadManifest:
    """
    Load a json manifest file and parse it into a DownloadManifest object.
    """
    # Check that the file path exists
    if not file_path.exists():
        # Create an empty manifest if it doesn't exist yet
        return DownloadManifest({})
    with open(file_path, 'r') as f:
        manifest_data = json.load(f)
    return DownloadManifest(**manifest_data)