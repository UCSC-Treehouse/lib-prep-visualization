from pydantic import BaseModel, field_validator
import json
from pathlib import Path
import scanpy as sc
import seaborn as sns
import matplotlib.pyplot as plt

class PlotConfig(BaseModel):
    src_adata_path: str
    plot_title: str
    meta_variable: str
    target_categories: list[str] = []

    @field_validator("src_adata_path")
    @classmethod
    def src_adata_path_must_exist(cls, v: str) -> str:
        # Make sure that the src_adata_path exists
        path = Path(v)
        if not path.exists():
            raise ValueError(f"src_adata_path {v} does not exist")
        return v

    @field_validator("src_adata_path")
    @classmethod
    def src_adata_path_must_be_h5ad(cls, v: str) -> str:
        # Make sure that the src_adata_path ends with .h5ad
        if not v.endswith(".h5ad"):
            raise ValueError("src_adata_path must be a path to a .h5ad file")
        return v


def load_plot_config(file_path: Path) -> PlotConfig:
    """
    Load a json config file and parse it into a PlotConfig object.
    """
    # Check that the file path exists
    if not file_path.exists():
        raise FileNotFoundError(f"Config file {file_path} does not exist.")
    
    # Read the file content
    with file_path.open("r") as f:
        config_data = json.load(f)
    
    # Parse the data into a PlotConfig object
    plot_config = PlotConfig(**config_data)
    
    return plot_config

def load_scanpy_adata(file_path: Path):
    """
    Load a scanpy AnnData object from the given file path.
    """
    adata = sc.read_h5ad(file_path)
    return adata

def validate_meta_variable(adata: sc.AnnData, plot_config: PlotConfig) -> bool:
    """
    Validate that the given meta_variable exists in the AnnData object's obs dataframe.
    """
    if plot_config.meta_variable not in adata.obs.columns:
        raise ValueError(f"meta_variable {plot_config.meta_variable} does not exist in the AnnData object's obs dataframe.")
    
    # Ensure that the targeted categories exist in the meta_variable column
    if plot_config.target_categories:
        existing_categories = adata.obs[plot_config.meta_variable].unique().tolist()
        for category in plot_config.target_categories:
            if category not in existing_categories:
                raise ValueError(f"target_category {category} does not exist in the meta_variable {plot_config.meta_variable}.")
    return True

def quick_seaborn_plot(adata: sc.AnnData, plot_config: PlotConfig):

    plt.figure(figsize=(10, 8))
    ax = sns.scatterplot(
        x=adata.obsm['X_umap'][:, 0],
        y=adata.obsm['X_umap'][:, 1],
        hue=adata.obs[plot_config.meta_variable],
        palette="tab10",
        alpha=0.7,
        edgecolor="none"
    )
    plt.title(plot_config.plot_title)
    plt.legend(title=plot_config.meta_variable)
    ax.set_xticks([])
    ax.set_yticks([])
    return plt