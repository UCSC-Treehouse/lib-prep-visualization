from pydantic import BaseModel, field_validator
import json
from pathlib import Path
import scanpy as sc
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


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

def validate_color_by(adata: sc.AnnData, label_key_config: ColorByConfig) -> bool:
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

def map_to_display_categories(adata: sc.AnnData, color_by: ColorByConfig, other_label: str = "other",) -> dict:
    """
    Map each observed value in `adata.obs[color_by.meta_key]` to a display category.

    Behavior:
    - If an observed value is present in `color_by.categories`, it maps to itself.
    - Otherwise it maps to `other_label`.
    - The returned mapping is a dict: {observed_value: display_category}.

    Args:
        adata: AnnData containing the column to color by in `adata.obs`.
        color_by: ColorByConfig containing `meta_key` and `categories` (the selected values).
        other_label: Label used for all values not explicitly listed in `color_by.categories`.

    Returns:
        mapping: dict mapping each unique observed value to the display category string.

    Raises:
        KeyError: if `color_by.meta_key` is not present in `adata.obs`.
    """
    col = color_by.meta_key
    if col not in adata.obs.columns:
        raise KeyError(f"Column {col} not found in adata.obs")

    observed = adata.obs[col].unique().tolist()
    category_set = set(color_by.categories)

    mapping = {}
    for v in observed:
        if v in category_set:
            mapping[v] = v
        else:
            mapping[v] = other_label

    return mapping

def gen_colormap(display_categories: dict, base_palette: str = "viridis") -> dict:
    """
    Generate a color map for the given display categories using a seaborn color palette.
    
    Args:
        display_categories: List of display category strings. {metadata_value: display_category}
        base_palette: Name of the seaborn color palette to use.
        
    Returns:
        color_map: Copy of display_categories dict but each value is now a tuple of the initial value and the assigned color.
        {metadata_value: (display_category, color)}
    """
    # determine unique display categories while preserving deterministic order
    unique_display_cats = pd.unique(list(display_categories.values())).tolist()

    n_colors = len(unique_display_cats)
    color_list = sns.color_palette(base_palette, n_colors=n_colors)

    # map display category -> color
    display_to_color = {cat: color_list[i] for i, cat in enumerate(unique_display_cats)}

    # build a mapping keyed by the original metadata observed values
    # each value is a tuple: (display_category, color)
    color_map = {
        meta_value: (display_cat, display_to_color[display_cat])
        for meta_value, display_cat in display_categories.items()
    }

    return color_map

def init_figure(plot_title: str):
    # figure size in inches
    width, height = 10, 8

    fig = plt.figure(figsize=(width, height))

    # Create a single Axes
    ax = plt.axes([0.1, 0.1, 0.8, 0.8])  # left, bottom, width, height (range 0 to 1)
    ax.set_title(plot_title)
    return fig, ax

def plot_points(adata: sc.AnnData, plot_config: PlotConfig, color_map: dict, ax: plt.Axes) -> None:
    """
    Plot the UMAP points from the AnnData object on the given Axes, coloring by the specified color map.
    Itterate through each sample in the addata. For each sample, get the metadata value for the given meta_variable defined in the
    plot_config. Cross reference that value with the color_map to get the display category and color. Plot the point with that color.

    Args:
        adata: AnnData containing UMAP coordinates in `adata.obsm['X_umap']` and metadata in `adata.obs`.
        plot_config: PlotConfig containing the color_by configuration.
        color_map: dict mapping display categories to (category, color) tuples.
        ax: Matplotlib Axes to plot on.
    """
    # Extract coordinates and metadata as arrays for vectorized access
    coords = adata.obsm['X_umap']
    meta_values = adata.obs[plot_config.color_by.meta_key].values

    # Loop through unique metadata categories instead of every cell
    for meta_value in np.unique(meta_values):
        # Boolean mask for the current group. Masking a numpy array was suggested by Copilot as a way to improve efficiency.
        mask = meta_values == meta_value
        # Get display name and color from map
        legend_label, color = color_map[meta_value]
        # Plot all points for this group at once
        ax.scatter(
            coords[mask, 0],
            coords[mask, 1],
            s=6,
            c=[color],
            label=legend_label,
            alpha=0.8,
            linewidths=0,
        )


def plot_umap(adata: sc.AnnData, plot_config: PlotConfig) -> plt.Figure:
    validate_color_by(adata, plot_config.color_by)
    display_categories = map_to_display_categories(adata, plot_config.color_by, other_label="other")
    color_map = gen_colormap(display_categories)
    fig, ax = init_figure(plot_config.plot_title)
    plot_points(adata, plot_config, color_map, ax)
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