# lib-prep-visualization
Visualization tool for comparing RNA-seq expression data across different library preparation methods using UMAP.

## Development Environment Setup

To create a development environment using conda:

```bash
conda env create -f environment.yaml
conda activate lib-prep-visualization
```

Make sure you have [conda](https://www.anaconda.com/download) installed.

# Scripts

This project features three scripts:
- `scripts/download_data.py`: Downloads gzipped datasets.
- `scripts/process_data.py`: Merges the downloaded datasets and performs UMAP dimensionality reduction.
- `scripts/plot_data.py`: Generates matplotlib visualizations from the processed data.

Each script accepts a command-line argument for a json configuration file that specifies parameters. Example configuration files are provided in the `config/` directory.

Here is an example of how to run each script:

```bash
python scripts/<script_name>.py --config <config_file>.json
```

## Download Data

### Quick Start

To download example datasets, run the following command:

```bash
python scripts/download_data.py --config <config_file>.json
```

<config_file>.json should point to a configuration file structured as follows:
```json
[
    {
        "compendia_id": <unique directory name safe string>,
        "expression_url": <url string>,
        "metadata_url": <url string>
    },
    {...}
]
```

### Implementation Details

The download data script accepts a configuration file specifying a list of online compendia to download.
Structure of the configuration file:

```json
[
    {
        "compendia_id": <string>,
        "expression_url": <string>,
        "metadata_url": <string>
    },
    {...}
]
```

Each compendia download target is a json object with three fields:
- `compendia_id`: A unique identifier for the compendia. This must be directory name safe.
- `expression_url`: URL to download the expression data `.tsv` or `.tsv.gz`.
- `metadata_url`: URL to download the metadata `.tsv` or `.tsv.gz`.

When the script runs it sets up a output directory structure like this:

```
data/
    <version>/
        <compendia_id1>/
        <compendia_id2>/
        ...
        download_manifest.json
        download.log
```

The script tracks all of it's file downloads in the `data/<version>/download_manifest.json` file.

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

Each file in the compendia has it's own manifest entry with the following fields:
- `last_download`: Timestamp of the last download attempt.
- `md5checksum`: Not implemented yet.
- `file_size`: Not implemented yet.
- `status`: Status of the download attempt. Either "success", "failed", or "incomplete".
- `software_version`: Version of the download script used for the download.

New files will be downloaded and added to the manifest. Existing files will be skipped under these conditions:
- The compendia exists in the `download_manifest.json` file.
- The `status` field the specific target file is "success".
- The `software_version` field matches the current version of the download script.

It is important to note that expression files and 
metadata files are treated separately. Downloading a new expression file will not automatically trigger a download of the corresponding metadata file.

Files are first downloaded into a temporary directory. Compendia files are often large and downloads can be interrupted. Downloading into a 
temporary directory helps prevent overwriting existing files with incomplete downloads. Once a file is fully downloaded, it is moved from the temporary directory to the final destination.

Steps of the download are logged to `data/<version>/download.log`.