from pydantic import BaseModel, field_validator
from pathlib import Path
import argparse
import json

import lib_prep_tools

DATA_DIR = Path.cwd() / 'data' / str(lib_prep_tools.__version__)
MS_BASE_DIR = Path.cwd() / 'matched_subsampled'

class MSConfig(BaseModel):
    """
    Matched Sampleing input json config
    """

    out_dir_name: str
    metadata_label: str
    compendia_set: set[str]

    @field_validator("out_dir_name")
    def validate_out_dir_name(cls, v):
        if not v:
            raise ValueError("out_dir_name must be a non-empty string")
        return v
    
    @field_validator("compendia_set")
    def validate_compendia_set_unique(cls, v):
        if len(v) < 2:
            raise ValueError("compendia_set must contain at least two compendia unique IDs")
        return v

    def validate_compendia_dirs_exist(self, base_path: Path) -> bool:
        for compendia_id in self.compendia_set:
            dir_path = base_path / compendia_id
            if not dir_path.exists() or not dir_path.is_dir():
                return False
        return True


def parse_args() -> Path:
    """
    Parse command line arguments to get the config file path.

    Returns:
        Path: Path to the input JSON config file given by --config argument.
    """
    parser = argparse.ArgumentParser(description="Matched Subsampling Script")
    parser.add_argument("--config", type=str, required=True, help="Path to the input JSON config file")
    config_path = Path(parser.parse_args().config)
    return config_path


def load_ms_config(config_fp: Path) -> MSConfig:
    """
    Load and validate the matched subsampling configuration from a JSON file.

    Args:
        config_fp (Path): Path to the JSON config file.

    Returns:
        MSConfig: Validated matched subsampling configuration object.
    """
    with open(config_fp, "r") as f:
        config_data = json.load(f)
    config = MSConfig.model_validate(config_data)
    if not config.validate_compendia_dirs_exist(DATA_DIR):
        raise ValueError("One or more compendia in compendia_list do not exist in the data directory.")
    return config

def main():
    config_fp = parse_args()
    ms_config = load_ms_config(config_fp)

if __name__ == "__main__":
    main()