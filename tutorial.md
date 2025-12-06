# Tutorial: Running Lib Prep Visualization Pipeline Locally in Conda Environment

This tutorial will guide you through the steps to run the Lib Prep Visualization pipeline locally using a Conda environment. Follow the instructions below to set up your environment, install dependencies, and execute the pipeline.

## Set up environment

Clone the repository to your local machine and navigate to the project directory:

```bash
git clone https://github.com/UCSC-Treehouse/lib-prep-visualization.git
cd lib-prep-visualization
```

Ensure you have conda installed: https://www.anaconda.com/download

Create and activate a Conda environment with the required dependencies and the `lib-prep-tools` package installed:

```bash
conda env create -f environment.yaml
conda activate lib-prep-visualization
```

## Quick Start Guide

### Step 1 (Optional): Download Treehouse Tumor Compendia

This tutorial will use a pilot dataset distributed with the repository. However, if you wish to download the full UCSC Treehouse tumor compendia, follow the instructions in this step.

Run the following command to download the two UCSC Treehouse tumor compendia (PolyA and RiboD):

- [Tumor Compendium 25.01 PolyA (January 2025)](https://treehousegenomics.soe.ucsc.edu/public-data/#tumor_25.01_polya)
- [Tumor Compendium 25.01 Ribodeplete (January 2025)](https://treehousegenomics.soe.ucsc.edu/public-data/#tumor_25.01_ribodeplete)

```bash
python scripts/download_data.py --config configs/download_data/polyA_vs_riboD_v25.01.json
```

The downloaded compendia files will be saved in the `data/` directory.

### Step 2: Process Data and Run UMAP Algorithm

Run the following command to merge all of the downloaded compendia and run the UMAP algorithm:

```bash
python scripts/process_data.py --config configs/process_data/pilot_data/pilot_data_process.json --data-dir pilot_data
```

The processed data with UMAP results will be saved in the `processed/pilot_data/` directory as `merged_compendia.hd5ad`.

### Step 3: Visualize UMAP Results
Run the following command generate a visualization coloring on library preparation method:

```bash
python scripts/plot_data.py --config configs/plot_data/pilot_data/pilot_compendia_type.json
```

The output visualization will be saved in the `figures/pilot_data` directory as `Pilot_Data_UMAP_Labeled_by_Library_Prep_Method.png`.

Next, plot a figure coloring on disease type.

```bash
python scripts/plot_data.py --config configs/plot_data/pilot_data/pilot_disease.json
```

The output visualization will be saved in the `figures/pilot_data` directory as `Pilot_Data_UMAP_Labeled_by_Disease.png`.

`Pilot_Data_UMAP_Labeled_by_Disease.png` uses the same legend colors as `Pilot_Data_UMAP_Labeled_by_Library_Prep_Method.png` for different values, which can be confusing.

To fix this, we can plot the disease type figure again using a custom color map.

```bash
python scripts/plot_data.py --config configs/plot_data/pilot_data/pilot_disease_cusom_colors.json
```

The output visualization will be saved in the `figures/pilot_data` directory as `Pilot_Data_UMAP_Custom_Colormap_by_Disease.png`.

## Advanced Features

### List Samples to Include in UMAP Analysis

You can hand select the samples to include in the UMAP analysis when running the `process_data.py` script. The following example selects 10 glioma and 10 synovial sarcoma samples from the two input compendia. The list of sample ids are provided to the `process_data.py` script through a `.tsv` file refrerenced in the configuration file.

```bash
python scripts/process_data.py --config configs/process_data/pilot_data/10_glioma_10_synovial_sarcoma.json --data-dir pilot_data
```

The output processed data with UMAP results for the selected samples will be saved in the `processed/pilot_data_glioma_ss` directory as `merged_compendia.hd5ad`.

To visualize the UMAP results for this subset of samples, run the following commands:

```bash
python scripts/plot_data.py --config configs/plot_data/pilot_data_glioma_ss/compendia_type.json
python scripts/plot_data.py --config configs/plot_data/pilot_data_glioma_ss/disease.json
```

The output visualizations will be saved in the `figures/pilot_data_glioma_ss` directory.


### Metadata Count-matched Subsampling

Sometimes one compendia may have significantly more samples than another compendia. In such cases, it is desirable to match the sample counts coming from each compendia based on a specific metadata. For example, if one compendia has more samples for disease types than another compendia, we may want to subsample the larger compendia to match the counts of each disease type in the smaller compendia. 

The `matched_subsampling.py` script performs count-matched subsampling based on a specified metadata column across multiple compendia and returns a list of sample IDs to include in the analysis. The output sample list can then be provided to the `process_data.py` script to generate UMAP results for the count-matched subsampled data.

The following example performs count-matched subsampling based on the `disease` metadata column when merging two input compendia.

```bash
python scripts/matched_subsampling.py --config configs/matched_subsampling/pilot_data/disease.json --data-dir pilot_data
```

The output sample list will be saved in the `matched_subsamples/pilot_data_disease_matched` directory as `subset_samples.tsv`.

Now we can run the `process_data.py` script using the output sample list to generate UMAP results for the count-matched subsampled data. Remember that the sample list is referenced in the configuration file.

```bash
python scripts/process_data.py --config configs/process_data/pilot_data/disease_matched.json --data-dir pilot_data
```

The output processed data with UMAP results for the count-matched subsampled disease data will be saved in the `processed/pilot_data_disease_matched` directory as `merged_compendia.hd5ad`.

To visualize the UMAP results for this count-matched subsampled data, run the following commands:

```bash
python scripts/plot_data.py --config configs/plot_data/pilot_data_disease_matched/compendia_type.json
python scripts/plot_data.py --config configs/plot_data/pilot_data_disease_matched/disease.json
```

View the output visualizations in the `figures/pilot_data_disease_matched` directory.