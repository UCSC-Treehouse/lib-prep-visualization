from pydantic import BaseModel, field_validator
import re
import json
from pathlib import Path

class CompendiaSource(BaseModel):
    """
    Model for a single compendia entry in the process_data config.
    """
    
    compendia_id: str
    lib_prep_type: str

    @field_validator("compendia_id")
    @classmethod
    def directory_name_safe(cls, v: str) -> str:
        # Make sure that the compendia_id is directory name safe. Precaution to make sure that no funny business happens with directory names.
        if not re.match(r"^[\w\-.]+$", v):
            raise ValueError(
                "compendia_id must be directory name safe (alphanumeric, dash, underscore, dot)"
            )
        return v
    
    @field_validator("lib_prep_type")
    @classmethod
    def valid_lib_prep_type(cls, v: str) -> str:
        # Make sure that the lib_prep_type is one of the accepted values.
        accepted_values = ["polya", "ribodepletion"]
        if v not in accepted_values:
            raise ValueError(f"lib_prep_type must be one of {accepted_values}")
        return v
    
class CompendiaListConfig(BaseModel):
    """
    Top-level model for the process_data JSON config.
    Attributes:
        compendia_list (list[CompendiaSource]): List of compendia sources to merge.
        ...More attributes on how to merge the data... (TBD)
    """
    
    compendia_list: list[CompendiaSource]

def load_config(file_path: Path) -> CompendiaListConfig:
    """
    TODO this should use a generic and be in a tools.py util module.

    Load a json config file and parse it into a DownloadListConfig object.
    """
    # Check that the file path exists
    if not file_path.exists():
        raise FileNotFoundError(f"Config file {file_path} does not exist.")
    with open(file_path, 'r') as f:
        config_data = json.load(f)
    return CompendiaListConfig.model_validate(config_data)