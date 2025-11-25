from pydantic import BaseModel, field_validator
import re
import json
from pathlib import Path
import pandas as pd
import scanpy as sc
import anndata
from . import logger


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
    
    def validate_id_dir(self, base_path: Path) -> bool:
        """
        Validate that the compendia_id directory for this source exists under the given base path.
        """
        dir_path = base_path / self.compendia_id
        return dir_path.exists() and dir_path.is_dir()

class CompendiaListConfig(BaseModel):
    """
    Top-level model for the process_data JSON config.
    Attributes:
        out_dir_name (Path): Directory name for the output data.
        sample_subset (Path, optional): Path to a file containing a subset of samples to include in the merged compendium.
        compendia_list (list[CompendiaSource]): List of compendia sources to merge.
        seed (int): Random seed for reproducibility.
    """
    
    out_dir_name: str
    sample_subset: str = None
    compendia_list: list[CompendiaSource]
    seed: int = 42  # Random seed for reproducibility

    @field_validator("out_dir_name")
    @classmethod
    def directory_name_safe(cls, v: str) -> str:
        # Make sure that the out_dir_name is directory name safe. Precaution to make sure that no funny business happens with directory names.
        if not re.match(r"^[\w\-.]+$", v):
            raise ValueError(
                "out_dir_name must be directory name safe (alphanumeric, dash, underscore, dot)"
            )
        return v

    @field_validator("sample_subset")
    @classmethod
    def sample_subset_safe(cls, v: str) -> str:
        if v and not Path(v).exists():
            raise ValueError(
                "sample_subset must be a valid file path"
            )
        return v

    @field_validator("seed")
    @classmethod
    def seed_must_be_integer(cls, v):
        if not isinstance(v, int):
            raise ValueError("Seed must be an integer.")
        return v

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

def validate_compendia_dirs(config: CompendiaListConfig, base_path: Path) -> bool:
    """
    Validate that the config compendia_id directories exist under the given base path.

    Returns:
        bool: True if all compendia_id directories exist, False otherwise.

    TODO This would be better off checking the manifest for 
    """
    return all(source.validate_id_dir(base_path) for source in config.compendia_list)

def validate_subsamples(merged_adata: anndata.AnnData, subset_ids: set) -> bool:
    """
    Validate that all sample IDs in the subset exist in the merged AnnData object.
    
    Args:
        merged_adata: AnnData object to check against
        subset_ids: Set of sample IDs to validate

    Returns:
        bool: True if all sample IDs in the subset exist in the merged AnnData object, False otherwise.

    This function was initially written by GithubCopilot using the docstring as a prompt and then iterated on by hand.
    """
    missing_ids = subset_ids - set(merged_adata.obs_names)
    
    if missing_ids:
        missing_count = len(missing_ids)
        if missing_count <= 10:
            logger.warning(f"Found {missing_count} sample IDs in subset file that are not in the merged AnnData object: {missing_ids}")
        else:
            sample_missing = list(missing_ids)[:10]
            logger.warning(f"Found {missing_count} sample IDs in subset file that are not in the merged AnnData object: {sample_missing} ... {missing_count - 10} more.")
        return False
    
    return True

def filter_samples_by_subset(merged_adata: anndata.AnnData, subset_file: str) -> anndata.AnnData:
    """
    Filter an AnnData object to only include samples from a subset file.
    
    Args:
        merged_adata: AnnData object to filter
        subset_file: Path to a file containing sample IDs (one per line, no header)
    
    Returns:
        Filtered AnnData object

    This function was initially written by GithubCopilot using the docstring as a prompt and then iterated on by hand.
    """
    logger.info(f"Filtering merged AnnData to only include samples from subset file: {subset_file}")
    subset_df = pd.read_csv(subset_file, header=None, names=["sample_id"])
    subset_ids = set(subset_df["sample_id"]) # convert to set to avoid duplicate sample_id lookups
    if not validate_subsamples(merged_adata, subset_ids):
        logger.warning("Subset validation failed. Skipping subsetting of AnnData object.")
        return merged_adata  # return unfiltered if validation fails
    initial_count = merged_adata.n_obs
    filtered_adata = merged_adata[merged_adata.obs_names.isin(subset_ids)].copy()
    final_count = filtered_adata.n_obs
    logger.info(f"Filtered samples from {initial_count} to {final_count} based on subset file.")
    return filtered_adata

def generate_h5ad_anndata(config: CompendiaListConfig, data_path: Path, output_path: Path):
    """
    Generate a merged umap reduced HDF5 AnnData file from the given compendia sources using scanpy. Save the result to the output_path.
    """
    
    logger.info(f"Building AnnData for {config.out_dir_name}.")
    
    if not validate_compendia_dirs(config, data_path):
        raise FileNotFoundError("One or more compendia_id directories do not exist under the given data_path.")

    # Running anndata concatenation object. After loading each compendia, we will merge it into this object.
    merged_adata = None

    for source in config.compendia_list:
        logger.info(f"Processing compendia_id: {source.compendia_id} of type {source.lib_prep_type}")
        comp_id = source.compendia_id
        exp_path = data_path / comp_id / "expression.tsv.gz"
        meta_path = data_path / comp_id / "metadata.tsv.gz"

        if not exp_path.exists():
            raise FileNotFoundError(f"Expression file not found for {comp_id}: {exp_path}")
        if not meta_path.exists():
            raise FileNotFoundError(f"Metadata file not found for {comp_id}: {meta_path}")

        # load expression (genes x samples), transpose to samples x genes
        logger.info(f"Loading expression data from {exp_path}")
        exp = pd.read_csv(exp_path, sep="\t", index_col=0).T
        logger.info(f"Loaded expression data shape: {exp.shape}")
        logger.info(f"Loading metadata from {meta_path}")
        meta = pd.read_csv(meta_path, sep="\t", index_col=0)
        logger.info(f"Loaded metadata shape: {meta.shape}")
        # Add compendia_type to metadata
        meta["compendia_type"] = source.lib_prep_type
        meta["compendia_id"] = source.compendia_id
        
        if set(exp.index) != set(meta.index):
            raise ValueError(f"Sample IDs in expression and metadata do not match for {comp_id}.")
        
        # Reindex metadata to match expression samples. It is much more effecient to match meta to exp than the other way around because the meta rows are much
        # smaller than the expression rows.
        meta = meta.reindex(exp.index)

        # Create AnnData object from the current processing compendia
        ad = sc.AnnData(exp, obs=meta)
        
        exp, meta = None, None  # free memory

        # Merge the compendia into the larger AnnData object
        logger.info(f"Merging compendia_id {comp_id} into the main AnnData object.")
        if merged_adata:
            merged_adata = anndata.concat(
                [merged_adata, ad],
                label="compendia_id",
                keys=[s.compendia_id for s in config.compendia_list],
                index_unique=None,
            )
        else:
            merged_adata = ad

        ad = None  # free memory

    logger.info(f"Total concatenated AnnData shape: {merged_adata.shape}")
    
    # If sample_subset is provided, filter the merged_adata to only include those samples
    if config.sample_subset:
        merged_adata = filter_samples_by_subset(merged_adata, config.sample_subset)

    logger.info(f"Running UMAP reduction.")
    # Run neighbors and UMAP on raw expression (no PCA, no filtering)
    sc.pp.neighbors(merged_adata, use_rep="X", random_state=config.seed)
    sc.tl.umap(merged_adata, random_state=config.seed)

    merged_adata.X = None  # Drop expression matrix to save space
    merged_adata.obsp = None  # also drop neighbor graph

    # Write AnnData to file
    logger.info(f"Writing AnnData to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_adata.write_h5ad(output_path)

