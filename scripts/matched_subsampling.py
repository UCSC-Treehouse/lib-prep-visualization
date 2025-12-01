from pydantic import BaseModel, field_validator
from pathlib import Path
import pandas as pd 
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
    seed: int = 42

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
        tuple[Path, Path]: Tuple containing the path to the input JSON config file and the data directory.
    """
    parser = argparse.ArgumentParser(description="Matched Subsampling Script")
    parser.add_argument("--config", type=str, required=True, help="Path to the input JSON config file")
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=DATA_DIR,
        help=(
            "Path to the directory containing downloaded data. "
            "The directory must match the output formatting of the download_data script."
        )
    )
    args = parser.parse_args()
    return args.config, args.data_dir


def load_ms_config(base_path: Path, config_fp: Path) -> MSConfig:
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
    if not config.validate_compendia_dirs_exist(base_path):
        raise ValueError("One or more compendia in compendia_list do not exist in the data directory.")
    return config


def load_metadata(base_dir: Path, compendia_id: str) -> pd.DataFrame:
    """
    Load metadata for a given compendia ID.

    Args:
        base_dir (Path): Base directory where compendia data is stored.
        compendia_id (str): The compendia unique identifier.

    Returns:
        pd.DataFrame: Metadata DataFrame for the specified compendia.
    """
    metadata_fp = base_dir / compendia_id / "metadata.tsv.gz"
    metadata_df = pd.read_csv(metadata_fp, sep='\t', compression='infer')
    return metadata_df


def validate_metadata_labels(meta_df_dict: dict[str, pd.DataFrame], label: str) -> bool:
    """
    Validate that the specified metadata label exists in all metadata DataFrames. If any DataFrame is missing the label, return False.
    """
    for meta_df in meta_df_dict.values():
        if label not in meta_df.columns:
            return False
    return True


def main():
    config_fp, data_dir = parse_args()
    # Load and validate matched subsampling config
    ms_config = load_ms_config(data_dir, config_fp)
    # Read in metadata for all compendia in the config set
    meta_df_dict = {comp_id: load_metadata(data_dir, comp_id) for comp_id in ms_config.compendia_set}
    # Validate that the metadata label exists in all compendia metadata
    if not validate_metadata_labels(meta_df_dict, ms_config.metadata_label):
        raise ValueError(f"Metadata label '{ms_config.metadata_label}' not found in all compendia metadata.")
    return

if __name__ == "__main__":
    main()