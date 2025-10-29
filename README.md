# lib-prep-visualization
Visualization tool for comparing RNA-seq expression data across different library preparation methods using UMAP.

## Development Environment Setup

To create a development environment using conda:

```bash
conda env create -f environment.yaml
conda activate lib-prep-visualization
```

Ensure you have conda installed: https://www.anaconda.com/download

## Project scripts

This repository includes three main scripts:

- `scripts/download_data.py` — downloads gzipped expression and metadata files.
- `scripts/process_data.py` — merges expression/metadata and runs UMAP.
- `scripts/plot_data.py` — creates figures from the processed data.

Each script accepts a `--config <config_file>.json` argument. Example configs are provided in the `config/` directory.

General usage:

```bash
python scripts/<script_name>.py --config <config_file>.json
```

## Download data

The download script retrieves expression and metadata files from specified URLs and organizes them into a structured directory layout.
These files are typically large, so the script is designed to handle interrupted downloads gracefully. Files will be prepared 
for downstream processing.

### Configuration format

The download script expects a JSON array of compendia objects. Example:

```json
[
    {
        "compendia_id": "Tumor_Compendium_25.01_PolyA_01_2025",
        "expression_url": "https://example.org/path/to/expression.tsv.gz",
        "metadata_url": "https://example.org/path/to/metadata.tsv.gz"
    },
    {
        "compendia_id": "another_compendia",
        "expression_url": "https://example.org/path/to/expression2.tsv.gz",
        "metadata_url": "https://example.org/path/to/metadata2.tsv.gz"
    }
]
```

- `compendia_id`: unique, directory-name-safe identifier used for the output folder.
- `expression_url`: URL to the expression file (`.tsv` or `.tsv.gz`).
- `metadata_url`: URL to the metadata file (`.tsv` or `.tsv.gz`).

### Download script methods

When run, the script creates the following directory layout under `data/`:

```
data/
    <version>/
        <compendia_id1>/
        <compendia_id2>/
        ...
        download_manifest.json
        download.log
```

The script tracks all of its file downloads in the `data/<version>/download_manifest.json` file.

Here is an example of the download manifest structure:

```json
{
    "Tumor_Compendium_25.01_PolyA_01_2025": {
        "expression": {
            "last_download": "0000-00-00T00:00:00.000000",
            "md5checksum": "",
            "file_size": 0,
            "status": "success",
            "software_version": "0.0.0"
        },
        "metadata": {
            "last_download": "0000-00-00T00:00:00.000000",
            "md5checksum": "",
            "file_size": 0,
            "status": "failed",
            "software_version": "0.0.0"
        }
    }, 
    "another_compendia": {...}
}
```

Each file in the compendia has its own manifest entry with the following fields:
- `last_download`: Timestamp of the last download attempt.
- `md5checksum`: Not yet implemented.
- `file_size`: Not yet implemented.
- `status`: Status of the download attempt: one of "success", "failed", or "incomplete".
- `software_version`: Version of the download script used.

New files will be downloaded and added to the manifest. Existing files will be skipped under these conditions:
- The compendia exists in the `download_manifest.json` file.
- The `status` field for the specific target file is "success".
- The `software_version` field matches the current version of the download script.

Expression files and metadata files are treated separately. Downloading a new expression file does not automatically trigger a download of the corresponding metadata file.

Files are first downloaded into a temporary directory because compendia files are often large and downloads can be interrupted. Downloading into a temporary directory helps prevent overwriting existing files with incomplete downloads. Once a file is fully downloaded, it is moved from the temporary directory to the final destination.

Log entries for downloads are appended to `data/<version>/download.log`.

## Process data

The process script merges multiple compendia expression and metadata files into a single Anndata object and runs UMAP for dimensionality reduction. This script will prepare data for plotting. 
The output is stored in a .hd5ad file which is compatible with the scanpy library and the UCSC Cell Browser.

### Configuration format

The configuration expects a JSON object with a list of compendia IDs to merge and process. Example:

```json
{
    "compendia_list": [
        {
            "compendia_id": "Tumor_Compendium_25.01_PolyA_01_2025",
            "lib_prep_type": "polya"
        },
        {
            "compendia_id": "Tumor_Compendium_25.01_RiboD_01_2025",
            "lib_prep_type": "ribodepletion"
        }
    ]
}
```

- `compendia_id`: unique identifier matching a downloaded compendia.
- `lib_prep_type`: library preparation type, either "polya" or "ribodepletion".

### Process script methods

For each compendia in the list, the process script will:
1. Load the expression and metadata files from the corresponding `data/<version>/<compendia_id>/` directory into Pandas Dataframes.
2. Transpose the expression dataframe so that genes are in columns and samples are in rows.
3. Column "compendia_type" is added to the metadata dataframe, populated with the `lib_prep_type` value from the config.
5. The expression and metdata dataframes are used to create a Anndata object.

Read more about Anndata here: https://anndata.readthedocs.io/en/stable/

Once each compendia from the config has been loaded into an Anndata object, the script will concatenate all of the Anndata objects into a single Anndata object.
This is preformed using the `anndata.concat()` method from the Anndata library, which concatenates row-wise (i.e., samples are stacked, genes are aligned).

The script then computes the neighbor graph and UMAP using the `scanpy` library and storing the results in the Anndata object.

Finally, the processed Anndata object is saved to `processed/processed_data.hd5ad`.

Logs for the script are saved to `processed/process.log`.