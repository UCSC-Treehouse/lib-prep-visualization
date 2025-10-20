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
    Group observed metadata values into display (legend) categories.

    Given an AnnData and a `ColorByConfig`, produce a mapping where keys are
    the display/legend labels and values are lists of the raw observed
    metadata values that should be shown under that legend label.

    Behavior:
    - If an observed value is present in `color_by.categories`, it is placed
      under its own display label (the same string).
    - Otherwise the observed value is placed under `other_label`.

    The returned dict preserves deterministic ordering: user-specified
    `color_by.categories` appear first in that order and `other_label` is appended when there are any
    non-selected observed values.

    Args:
        adata: AnnData containing the column to color by in `adata.obs`.
        color_by: ColorByConfig containing `meta_key` and `categories`.
        other_label: Label used for all values not explicitly listed in
            `color_by.categories`.

    Returns:
        dict: {display_label: [metadata_value, ...]}
    """
    col = color_by.meta_key
    # Preserve the user-provided category order; create empty lists for them
    members: dict = {cat: [] for cat in color_by.categories}
    category_set = set(color_by.categories)

    # Iterate observed values in first-seen order and assign to buckets
    observed = pd.unique(adata.obs[col]).tolist()
    for v in observed:
        if v in category_set:
            members.setdefault(v, []).append(v)
        else:
            members.setdefault(other_label, []).append(v)

    return members

def gen_colormap(display_categories: dict, base_palette: str = "tab10") -> dict:
    """
    Generate a color map for each display (legend) category.

    Args:
        display_categories: dict {display_label: [metadata_value, ...]}
        base_palette: Name of a seaborn color palette (passed to `seaborn.color_palette`).

    Returns:
        dict: Mapping display_label -> (color) where:
            - color is a RGB tuple color from the seaborn palette
    """
    # display_categories is now expected to be {display_label: [meta_values]}
    display_cats = list(display_categories.keys())
    n_colors = len(display_cats)
    color_list = sns.color_palette(base_palette, n_colors=n_colors)
    color_map = {}
    for i, disp in enumerate(display_cats):
        color_map[disp] = color_list[i]
    return color_map

def init_figure(plot_title: str):
    # figure size in inches
    width, height = 10, 8

    fig = plt.figure(figsize=(width, height))

    # Create a single Axes
    ax = plt.axes([0.1, 0.1, 0.8, 0.8])  # left, bottom, width, height (range 0 to 1)
    ax.set_title(plot_title)
    return fig, ax

def plot_points(adata: sc.AnnData, plot_config: PlotConfig, display_categories: dict, color_map: dict, ax: plt.Axes) -> None:
    """
    Plot the UMAP points from the AnnData object on the given Axes. Points are grouped based on the display categories parameter
    and colored according to the color map.

    Args:
        adata: AnnData containing UMAP coordinates in `adata.obsm['X_umap']` and metadata in `adata.obs`.
        plot_config: PlotConfig containing the color_by configuration.
        display_categories: dict mapping display categories to lists of metadata values.
        color_map: dict mapping display categories to RGB tuple colors.
        ax: Matplotlib Axes to plot on.
    """
    # Extract coordinates and metadata as arrays for vectorized access
    coords = adata.obsm['X_umap']
    meta_values = adata.obs[plot_config.color_by.meta_key].values

    for legend_label, group_meta_values in display_categories.items():
        # Create a boolean mask for all metadata values that map to this legend label
        mask = np.isin(meta_values, group_meta_values)
        color = color_map[legend_label]
        
        # Plot the other label points behind the rest
        zorder = 0 if legend_label == "other" else 1

        ax.scatter(
            coords[mask, 0],
            coords[mask, 1],
            c=[color],
            label=legend_label,
            alpha=1.0,
            edgecolor="none",
            s=30,  # point size
            zorder=zorder
        )

def add_legend(ax: plt.Axes) -> None:
    """
    Add a legend to the given Axes.
    """
    ax.legend(
        title="Categories",
        loc="best",
        fontsize="small",
        title_fontsize="medium",
        frameon=True,
        framealpha=0.9,
        edgecolor="black",
    )

def plot_umap(adata: sc.AnnData, plot_config: PlotConfig) -> plt.Figure:
    validate_color_by(adata, plot_config.color_by)
    display_categories = map_to_display_categories(adata, plot_config.color_by, other_label="other")
    color_map = gen_colormap(display_categories)
    fig, ax = init_figure(plot_config.plot_title)
    plot_points(adata, plot_config, display_categories, color_map, ax)
    add_legend(ax)
    return fig
