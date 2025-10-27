# lib-prep-visualization
Visualization tool for comparing RNA-seq expression data across different library preparation methods using UMAP.

## Development Environment Setup

To create a development environment using conda:

```bash
conda env create -f environment.yaml
conda activate lib-prep-visualization
```

Make sure you have [conda](https://www.anaconda.com/download) installed.

# Documentation

This project features three scripts:
- `scripts/download_data.py`: Downloads gzipped datasets.
- `scripts/process_data.py`: Merges the downloaded datasets and performs UMAP dimensionality reduction.
- `scripts/plot_data.py`: Generates matplotlib visualizations from the processed data.

Each script accepts a command-line argument for a json configuration file that specifies parameters. Example configuration files are provided in the `config/` directory.

Here is an example of how to run each script:

```bash
python scripts/<script_name>.py --config <config_file>.json
```
