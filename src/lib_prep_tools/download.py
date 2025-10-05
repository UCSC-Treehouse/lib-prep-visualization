from wsgiref.simple_server import software_version
from pydantic import BaseModel, HttpUrl, field_validator, RootModel, ValidationError
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import re
import json
import requests

import lib_prep_tools

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


class ManifestFileStatusEntry(BaseModel):
    last_download: datetime = None
    md5checksum: str = ""
    file_size: int = 0
    status: str = STATUS_IN_PROGRESS
    software_version: str = lib_prep_tools.__version__

    model_config = {
        "validate_assignment": True  # validates any field change
    }

class ManifestCompendiaEntry(BaseModel):
    expression: ManifestFileStatusEntry
    metadata: ManifestFileStatusEntry

class DownloadManifest(RootModel[Dict[str, ManifestCompendiaEntry]]):

    def add_entry(self, name: str, entry: ManifestCompendiaEntry):
        """Add a new compendia entry under the given name."""
        if not isinstance(entry, ManifestCompendiaEntry):
            raise TypeError("entry must be a ManifestCompendiaEntry instance")
        self.root[name] = entry

    def get_entry(self, name: str) -> ManifestCompendiaEntry:
        """Retrieve an existing compendia entry."""
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
    Load a json manifest file and parse it into a DownloadManifest object. If the file does not exist, return an empty manifest.
    If the file exists but fails the validation for the DownloadManifest model, return an empty manifest.
    """
    # Check that the file path exists
    if not file_path.exists():
        # Create an empty manifest if it doesn't exist yet
        return DownloadManifest({})
    with open(file_path, 'r') as f:
        manifest_data = json.load(f)
    try:
        return DownloadManifest(manifest_data)
    except ValidationError:
        # If the manifest is invalid, return an empty manifest
        return DownloadManifest({})

def file_status_need_download(file_status_entry: ManifestFileStatusEntry, software_version: str) -> bool:
    """
    Determine if a file needs to be downloaded based on the manifest file status entry. Return True if the status is not 
    'success', or if the software version does not match.

    This function was written with the help of GitHub copilot. The docstring was used as the prompt.
    """
    if file_status_entry.status != STATUS_SUCCESS:
        return True
    if file_status_entry.software_version != software_version:
        return True
    return False

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

def get_or_create_manifest_entry(manifest: DownloadManifest, compendia_id: str) -> ManifestCompendiaEntry:
    """
    Retrieve an existing manifest entry for the given compendia_id, or create a new one if it doesn't exist.

    This function was drafted with the help of GitHub copilot. The function name was used as a tab complete.
    """
    if compendia_id not in manifest.root:
        manifest.add_entry(compendia_id, ManifestCompendiaEntry(
            expression=ManifestFileStatusEntry(),
            metadata=ManifestFileStatusEntry()
        ))
    return manifest.get_entry(compendia_id)

def download_file_with_manifest_update(url: HttpUrl, target_path: Path, manifest_entry: ManifestFileStatusEntry, version: str) -> bool:
    """
    Download a file from a URL to the target path, and update the manifest entry accordingly.
    Return the target path if successful, or None if the download fails.

    Returns
        bool: True if download was successful, False otherwise.

    This function was drafted with the help of GitHub copilot. The function name was used as a tab complete.
    """
    downloaded_path = download_file(url, target_path)
    if downloaded_path:
        manifest_entry.last_download = datetime.now()
        manifest_entry.status = STATUS_SUCCESS
        manifest_entry.software_version = version
        return True
    else:
        manifest_entry.status = STATUS_FAILED
        return False

def download_compendia(download_list_config: DownloadListConfig, download_manifest: DownloadManifest, data_dir: Path, version: str) -> DownloadManifest:
    for compendia_download_config in download_list_config.root:
        compendia_id = compendia_download_config.compendia_id
        target_dir = data_dir / compendia_id
        target_dir.mkdir(parents=True, exist_ok=True)

        manifest_entry = get_or_create_manifest_entry(download_manifest, compendia_id)

        exp_manifest_file_status = manifest_entry.expression
        if file_status_need_download(exp_manifest_file_status, version):
            expression_url = compendia_download_config.expression_url
            exp_path = target_dir / "expression.tsv.gz"
            download_file_with_manifest_update(expression_url, exp_path, exp_manifest_file_status, version)
        
        meta_manifest_file_status = manifest_entry.metadata
        if file_status_need_download(meta_manifest_file_status, version):
            metadata_url = compendia_download_config.metadata_url
            meta_path = target_dir / "metadata.tsv.gz"
            download_file_with_manifest_update(metadata_url, meta_path, meta_manifest_file_status, version)    

    return download_manifest
