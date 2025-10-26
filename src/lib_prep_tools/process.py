from pydantic import BaseModel, field_validator
import re
import json
from pathlib import Path

import pandas as pd
import scanpy as sc
import anndata

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

def validate_compendia_dirs(config: CompendiaListConfig, base_path: Path) -> bool:
    """
    Validate that the config compendia_id directories exist under the given base path.

    Returns:
        bool: True if all compendia_id directories exist, False otherwise.

    TODO This would be better off checking the manifest for 
    """
    return all(source.validate_id_dir(base_path) for source in config.compendia_list)

def generate_hdf5_anndata(config: CompendiaListConfig, data_path: Path, output_path: Path):
    """
    Generate a merged umap reduced HDF5 AnnData file from the given compendia sources using scanpy. Save the result to the output_path.
    """
    if not validate_compendia_dirs(config, data_path):
        raise FileNotFoundError("One or more compendia_id directories do not exist under the given data_path.")

    # Build one AnnData per compendia, store in list for merging
    adata_list = []

    for source in config.compendia_list:
        comp_id = source.compendia_id
        exp_path = data_path / comp_id / "expression.tsv.gz"
        meta_path = data_path / comp_id / "metadata.tsv.gz"

        if not exp_path.exists():
            raise FileNotFoundError(f"Expression file not found for {comp_id}: {exp_path}")
        if not meta_path.exists():
            raise FileNotFoundError(f"Metadata file not found for {comp_id}: {meta_path}")

        # load expression (genes x samples), transpose to samples x genes
        exp = pd.read_csv(exp_path, sep="\t", index_col=0).T
        meta = pd.read_csv(meta_path, sep="\t", index_col=0)
        # Add compendia_type to metadata
        meta["compendia_type"] = source.lib_prep_type
        meta["compendia_id"] = source.compendia_id
        
        if set(exp.index) != set(meta.index):
            raise ValueError(f"Sample IDs in expression and metadata do not match for {comp_id}.")
        
        # Reindex metadata to match expression samples. It is much more effecient to match meta to exp than the other way around because the meta rows are much
        # smaller than the expression rows.
        meta = meta.reindex(exp.index)

        ad = sc.AnnData(exp, obs=meta)
        adata_list.append(ad)

    # Concatenate all AnnData objects
    adata = anndata.concat(
        adata_list,
        label="compendia_id",
        keys=[s.compendia_id for s in config.compendia_list],
        index_unique=None,
    )

    # Run neighbors and UMAP on raw expression (no PCA, no filtering)
    sc.pp.neighbors(adata, use_rep="X")
    sc.tl.umap(adata)

    # Write AnnData to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(output_path)

