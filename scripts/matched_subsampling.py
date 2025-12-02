from pydantic import BaseModel, field_validator
from pathlib import Path
import pandas as pd 
import argparse
import json
import random

import lib_prep_tools

DATA_DIR = Path.cwd() / 'data' / str(lib_prep_tools.__version__)
MS_BASE_DIR = Path.cwd() / 'matched_subsamples'

class MSConfig(BaseModel):
    """
    Matched Sampling input json config
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


def compute_min_sample_counts(meta_df_dict: dict[str, pd.DataFrame], column_label: str) -> dict[str, int]:
    """
    Generate a dictionary mapping each unique column entry to the minimum number of samples 
    in a single metadata df that have that label value.
    
    For example, if column_label='disease' and 'neuroblastoma' appears 100 times in compendia A 
    and 50 times in compendia B, the result will include {'neuroblastoma': 50}.
    
    Args:
        meta_df_dict: Dictionary mapping compendia IDs to their metadata DataFrames
        column_label: The metadata column name to analyze
        
    Returns:
        Dictionary mapping label values to their minimum count across all compendia

    GithubCopilot:
    Context: tests/test_matched_subsampling.py
    Prompt: "Implement this function using the docstring and tests as a guide"

    Itterated by hand afterwards. In-line comments added by hand.
    """

    # Dictionary of every unique entry for a given metdata column across all compendia to a list of counts. Each compendia that contains at least 1 instance of that entry will contribute a count to the list.
    # If key "A" has a list value of [10, 5, 20], that means 3 compendia have at least one instance of "A" in the specified column, with counts of 10, 5, and 20 respectively.
    label_counts: dict[str, list[int]] = {}
    
    # Build label_counts dictionary using each compendia's metadata
    for meta_df in meta_df_dict.values():
        # If a column is missing from a metadata df, then the min_sample_counts must be empty so can return early
        if column_label not in meta_df.columns:
            return {}
        # Get value counts for the specified column in the current metadata df
        value_counts = meta_df[column_label].value_counts()
        # Update label_counts with counts from the current metadata df
        for label_value, count in value_counts.items():
            if label_value not in label_counts:
                label_counts[label_value] = []
            label_counts[label_value].append(count)
    
    # Only include column entries that appear in ALL compendia (have counts from all dataframes). If metdata_df_1 has "A" and "B", and metadata_df_2 has "B" and "C",
    # then only "B" will be included in the result because it's counts list will have length 2 (one from each compendia), while "A" and "C" will only have length 1.
    num_compendia_with_entry = sum(1 for df in meta_df_dict.values() if column_label in df.columns)
    min_sample_counts = {
        label_value: min(counts) 
        for label_value, counts in label_counts.items() 
        if len(counts) == num_compendia_with_entry
    }
    
    return min_sample_counts


def create_sample_subset_list(meta_df_dict: dict[str, pd.DataFrame], column_name: str, min_sample_counts: dict[str, int], seed: int) -> list[str]:
    """
    Create a list of sample IDs by selecting a random subset of samples based on the minimum sample counts per column entry.

    Args:
        meta_df_dict: Dictionary mapping compendia IDs to their metadata DataFrames
        column_name: The metadata column name to use for subsampling
        min_sample_counts: Dictionary mapping column entry values to their minimum count across all compendia
        seed: Random seed for reproducibility
    """
    subset_sample_ids = []
    for _, meta_df in meta_df_dict.items():
        for label_value, count in min_sample_counts.items():
            # Filter metadata df to only include rows with the current label value
            matching_samples = meta_df[meta_df[column_name] == label_value]
            # Randomly sample the required number of samples for this label value
            sampled_ids = matching_samples.sample(n=count, random_state=seed)['th_dataset_id'].tolist()
            subset_sample_ids.extend(sampled_ids)
    return subset_sample_ids


def write_sample_subset_file(sample_ids: list[str], output_fp: Path):
    """
    Write the list of sample IDs to a subset file.

    Args:
        sample_ids: List of sample IDs to write
        output_fp: Path to the output subset file
    """
    with open(output_fp, "w") as f:
        for sample_id in sample_ids:
            f.write(f"{sample_id}\n")


def main():
    config_fp, data_dir = parse_args()
    # Load and validate matched subsampling config
    ms_config = load_ms_config(data_dir, config_fp)
    # Read in metadata for all compendia in the config set
    meta_df_dict = {comp_id: load_metadata(data_dir, comp_id) for comp_id in ms_config.compendia_set}
    # Validate that the metadata label exists in all compendia metadata
    if not validate_metadata_labels(meta_df_dict, ms_config.metadata_label):
        raise ValueError(f"Metadata label '{ms_config.metadata_label}' not found in all compendia metadata.")
    # Compute minimum sample counts for each unique entry in the specified metadata column
    min_sample_counts = compute_min_sample_counts(meta_df_dict, ms_config.metadata_label)
    sample_list = create_sample_subset_list(meta_df_dict, ms_config.metadata_label, min_sample_counts, ms_config.seed)
    # Write sample IDs to output file
    output_dir = MS_BASE_DIR / ms_config.out_dir_name / "subset_samples.tsv"
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    write_sample_subset_file(sample_list, output_dir)

if __name__ == "__main__":
    main()