from pydantic import BaseModel, field_validator, ValidationError
import json
from pathlib import Path

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
            raise ValidationError(f"src_adata_path {v} does not exist")
        return v

    @field_validator("src_adata_path")
    @classmethod
    def src_adata_path_must_be_h5ad(cls, v: str) -> str:
        # Make sure that the src_adata_path ends with .h5ad
        if not v.endswith(".h5ad"):
            raise ValidationError("src_adata_path must be a path to a .h5ad file")
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