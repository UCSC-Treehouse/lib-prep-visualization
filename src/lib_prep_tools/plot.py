from pydantic import BaseModel, field_validator
import json
from pathlib import Path
import scanpy as sc
import seaborn as sns
import matplotlib.pyplot as plt


class ColorByConfig(BaseModel):
    """
    Model for the label_key config in the plot config. This will hold the meta_variable to color by and the target 
    categories to assign individual colors.
    """
    meta_key: str
    categories: list[str] = []


class PlotConfig(BaseModel):
    src_adata_path: str
    plot_title: str
    color_by: ColorByConfig

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
    
    return PlotConfig.model_validate(config_data)

def load_scanpy_adata(file_path: Path):
    """
    Load a scanpy AnnData object from the given file path.
    """
    adata = sc.read_h5ad(file_path)
    return adata

def validate_meta_variable(adata: sc.AnnData, label_key_config: ColorByConfig) -> bool:
    """
    Validate that the given meta_variable exists in the AnnData object's obs dataframe.
    """
    if label_key_config.meta_key not in adata.obs.columns:
        raise ValueError(f"meta_variable {label_key_config.meta_key} does not exist in the AnnData object's obs dataframe.")
    
    # Ensure that the targeted categories exist in the meta_variable column
    if label_key_config.categories:
        existing_categories = adata.obs[label_key_config.meta_key].unique().tolist()
        for category in label_key_config.categories:
            if category not in existing_categories:
                raise ValueError(f"target_category {category} does not exist in the meta_variable {label_key_config.meta_key}.")
    return True

def init_figure(plot_title: str):
    # figure size in inches
    width, height = 10, 8

    fig = plt.figure(figsize=(width, height))

    # Create a single Axes
    ax = plt.axes([0.1, 0.1, 0.8, 0.8])  # left, bottom, width, height (range 0 to 1)
    ax.set_title(plot_title)
    return fig, ax

def plot_umap(adata: sc.AnnData, plot_config: PlotConfig) -> plt.Figure:
    fig, ax = init_figure(plot_config.plot_title)
    return fig

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