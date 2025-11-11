# Tutorial: Running Lib Prep Visualization Pipeline Locally in Conda Environment

This tutorial will guide you through the steps to run the Lib Prep Visualization pipeline locally using a Conda environment. Follow the instructions below to set up your environment, install dependencies, and execute the pipeline.

## Step 1: Set up environment

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

## Step 2: Downlaod Treehouse Tumor Compendia

Run the following command to download the two UCSC Treehouse tumor compendia (PolyA and RiboD):

- [Tumor Compendium 25.01 PolyA (January 2025)](https://treehousegenomics.soe.ucsc.edu/public-data/#tumor_25.01_polya)
- [Tumor Compendium 25.01 Ribodeplete (January 2025)](https://treehousegenomics.soe.ucsc.edu/public-data/#tumor_25.01_ribodeplete)

```bash
python scripts/download_data.py --config configs/download_data/polyA_vs_riboD_v25.01.json
```

The downloaded compendia files will be saved in the `data/` directory.

## Step 3: Process Data and Run UMAP Algorithm

Run the following command to merge all of the downloaded compendia and run the UMAP algorithm:

```bash
python scripts/process_data.py --config configs/process_data/polyA_vs_riboD_v25-01/polyA_vs_riboD_v25.01.json
```

The processed data with UMAP results will be saved in the `processed/polyA_vs_riboD_v25-01/` directory as `processed_data.hd5ad`.

## Step 4: Visualize UMAP Results
Run the following command generate a visualization coloring on library preparation method:

```bash
python scripts/plot_data.py --config configs/plot_data/polyA_vs_riboD_v25-01/polyA_vs_riboD_v25.01.json
```

The output visualization will be saved in the `figures/` directory as `UMAP_Labeled_by_Library_Prep_Method.png`.

Next, plot a figure labeling medulloblastoma samples and synovial sarcoma samples. This time we will use a custom color palette instead of the default seaborn color palette.

```bash
python scripts/plot_data.py --config configs/plot_data/polyA_vs_riboD_v25-01/medulloblastoma_vs_synovial_sarcoma.json
```

The output visualization will be saved in the `figures/` directory as `UMAP_Medulloblastoma_and_Synovial_Sarcoma.png`.

Finally, we will use a config which assigns custom metadata labels that group medulloblastoma and synovial sarcoma samples by their library preparation method. The custom labels can be found
in `configs/custom_metadata/libprep_disease_mb_synsarc.tsv`

```bash
python scripts/plot_data.py --config configs/plot_data/polyA_vs_riboD_v25-01/polya_ribod_medulloblastoma_synovial_sarcoma.json
```

The output visualization will be saved in the `figures/` directory as `UMAP_PolyA_and_Ribodepletion_Medulloblastoma_and_Synovial_Sarcoma.png`.