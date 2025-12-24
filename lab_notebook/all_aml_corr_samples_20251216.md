# Correlated ALL and AML Samples in PolyA and RiboD Preps

This notebook explores visualizations of correlated ALL and AML samples from the PolyA and RiboD prep compendia.

Here are the steps taken to generate the data and plots:

### 1. Build Sample Subset List

Run the `matched_subsampling.py` script to generate a subset of samples of the polyA and RiboD v25-01 compendia that contain identical samples counts for each disease. The output is saved to `matched_subsamples/polyA_riboD_disease_matched/subset_samples.tsv`.
```bash
python scripts/matched_subsampling.py --config configs/matched_subsampling/polyA_vs_riboD_v25-01/disease.json
```

`matched_subsampling.py` picks random samples for each disease in a compendia that needs to be downsampled to match the sample counts of the compendia with the fewest samples for that disease. The list of samples we are interested in labeling can be found in `configs/plot_data/polyA_riboD_disease_matched/filtered_ALL_AML_list.tsv`. Copy `matched_subsamples/polyA_riboD_disease_matched/subset_samples.tsv` to `matched_subsamples/polyA_riboD_disease_matched/all_aml_selected_samples_20251216.tsv` and manually add the additional ALL and AML samples to the list that were not included in the random sampling. This ensures that all highest correlated samples are included in the final plots. Then to keep the sample counts balanced, remove non-top 80 correlated samples from each disease group as needed. Below are the samples to add and remove by hand.

**Samples to add by hand:**

ALL PolyA:
```
THR24_1644_S01
THR24_1591_S01
TARGET-10-PARARJ-09
TARGET-10-PANSHK-04
TARGET-10-PAPIYG-03B-01R
THR24_1576_S01
THR24_1630_S01
THR24_1602_S01
TARGET-10-PASNJI-09B-01R
```

AML PolyA:
```
TARGET-20-PASKUA-09A-01R
THR24_1733_S01
TARGET-20-PALFVW-09A-01R
TARGET-20-PATELT-03
TARGET-20-PARXNG-09
TCGA-AB-2900-03
TARGET-20-PARYFN-04
TCGA-AB-3002-03
TCGA-AB-2810-03
TARGET-20-PARSAN-03
TARGET-20-PASTUH-03
TARGET-20-PAPVDV-03
TARGET-20-PAPAEG-09A-01R
TARGET-20-PASKGH-09A-01R
TARGET-20-PASGGK-03
TARGET-20-PASHWN-09A-01R
TARGET-20-PARTST-09A-02R
TARGET-20-PARTXH-09A-02R
```

**Samples to remove by hand to keep sample counts balanced between ALL and AML PolyA samples (remove non-top 80 correlated samples):**

Non-top 80 correlated ALL PolyA Samples removed to keep sample counts balanced:
```
TARGET-10-PATLMA-03A-01R
TARGET-10-PASWNU-09A-01R
THR24_2118_S01
TH27_1242_S01
THR24_1882_S01
TARGET-10-PARWLP-09A-01R
THR08_0203_S01
TARGET-10-PANRWG-09
THR24_1703_S01
```

Non-top 80 correlated AML PolyA Samples removed to keep sample counts balanced:
```
TCGA-AB-2893-03
TARGET-20-PARVSF-09A-02R
THR24_1706_S01
TARGET-20-PARAJX-09
TARGET-20-PASMYS-04
TARGET-20-PASMGW-09
TARGET-20-PASVVS-09
TCGA-AB-3011-03
THR24_1726_S01
TCGA-AB-2952-03
TARGET-20-PAPXUF-09A-01R
TARGET-20-PASFLM-09
TCGA-AB-2869-03
TARGET-20-PANCSC-09
TCGA-AB-2837-03
TCGA-AB-2959-03
TH27_2669_S01
TCGA-AB-3007-03
```

### 2. Process Data with Selected Samples

Run the `process_data.py` script with the updated sample subset file to generate the processed compendia containing only the selected ALL and AML samples. The output will be saved to `processed/polyA_riboD_all_aml_disease_matched/merged_compendia.h5ad`.
```bash
python scripts/process_data.py --config configs/process_data/polyA_vs_riboD_disease_matched/all_aml_disease_and_selected.json
```

### 3. Plot Data

For general reference, plot compendia type and top 10 diseases:
```bash
python scripts/plot_data.py --config configs/plot_data/polyA_riboD_all_aml_disease_matched/10_most_sampled_diseases.json
python scripts/plot_data.py --config configs/plot_data/polyA_riboD_all_aml_disease_matched/compendia_type.json
```

Plot with ALL and AML samples highlighted and colored by disease and prep type:
```bash
python scripts/plot_data.py --config configs/plot_data/polyA_riboD_all_aml_disease_matched/filtered_ALL_AML_2025_12_16.json
```

Plot the dataset source of the most correlated ALL and AML samples with three different plot orders to ensure visibility of all dataset sources:
```bash
python scripts/plot_data.py --config configs/plot_data/polyA_riboD_all_aml_disease_matched/dataset_src_order_a.json
python scripts/plot_data.py --config configs/plot_data/polyA_riboD_all_aml_disease_matched/dataset_src_order_b.json
python scripts/plot_data.py --config configs/plot_data/polyA_riboD_all_aml_disease_matched/dataset_src_order_c.json
```

Find all results in the `figures/polyA_riboD_all_aml_disease_matched/` directory.