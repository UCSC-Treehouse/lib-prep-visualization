from pydantic import BaseModel, HttpUrl, field_validator, RootModel
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import re
import json
import requests

# Manifest Dataset Status Options
STATUS_IN_PROGRESS = "in_progress"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"


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


class DownloadListConfig(RootModel[List[CompendiaDownloadConfig]]):
    pass


class ManifestEntry(BaseModel):
    last_download: datetime
    md5checksum: str
    file_size: int
    status: str
    software_version: str

    model_config = {
        "validate_assignment": True  # validates any field change
    }

class DownloadManifest(RootModel):
    root: Dict[str, ManifestEntry]

    def add_entry(self, name: str, entry: ManifestEntry):
        """Add a new ManifestEntry under the given name."""
        if not isinstance(entry, ManifestEntry):
            raise TypeError("entry must be a ManifestEntry instance")
        self.root[name] = entry

    def get_entry(self, name: str) -> ManifestEntry:
        """Retrieve an existing ManifestEntry for modification."""
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
    return DownloadListConfig(config_data)


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

def download_file(url: HttpUrl, target_path: Path, chunk_size: int = 10*1024*1024) -> Optional[Path]:
    """
    Download a file from a URL to the target path. Return None if the file download fails.

    This function was written with the help of GitHub copilot. The docstring was used as the prompt.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an error for bad responses
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)
        return target_path
    except requests.RequestException:
        return None

def download_compendia(download_list_config: DownloadListConfig, manifest_path: DownloadManifest, data_dir: Path, software_version: str):
    """
    File download steps:
    - get compendia target from download list
    - create target directory if it doesn't exist
    - add entry to manifest marking as 'in_progress' with current software version
    - download clinical and manifest file to temp directory
    - compute md5 checksum and file size
    - move files to target directory
    - update manifest entry with checksum, file size, status 'downloaded', and current timestamp
    """
    manifest_fp = data_dir / 'download_manifest.json'
    for compendia_download_config in download_list_config.root:
        compendia_id = compendia_download_config.compendia_id
        target_dir = data_dir / compendia_id
        target_dir.mkdir(parents=True, exist_ok=True)
        log_fp = target_dir / 'download.log'
        if not log_fp.exists():
            log_fp.touch()

        # Add or update entry in manifest marking as 'in_progress'
        manifest_entry = ManifestEntry(
            last_download=datetime.now(),
            md5checksum="",
            file_size=0,
            status=STATUS_IN_PROGRESS,
            software_version=software_version
        )
        manifest_path.add_entry(compendia_id, manifest_entry)

        # Download expression and metadata files
        expression_fp = target_dir / "expression.tsv.gz"
        downloaded_expression_fp = download_file(compendia_download_config.expression_url, expression_fp)

        metadata_fp = target_dir / "metadata.tsv.gz"
        downloaded_metadata_fp = download_file(compendia_download_config.metadata_url, metadata_fp)

        if not expression_fp or not metadata_fp:
            # Update manifest entry marking as 'failed'
            manifest_entry.status = STATUS_FAILED
            manifest_entry.last_download = datetime.now()
            manifest_path.add_entry(compendia_id, manifest_entry)
            continue
        else:
            manifest_entry.status = STATUS_SUCCESS
            manifest_entry.last_download = datetime.now()
            manifest_path.add_entry(compendia_id, manifest_entry)

    # Write the manifest back to disk
    with open(manifest_fp, 'w') as f:
        json.dump(manifest_path.model_dump(), f, indent=4, default=str)  # default=str to handle datetime serialization
