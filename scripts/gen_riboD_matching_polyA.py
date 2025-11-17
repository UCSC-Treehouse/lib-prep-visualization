from pathlib import Path
import pandas as pd
import numpy as np
import scanpy as sc
import anndata as ad


def generate_anndata_from_compendia_dir(dir: Path, compendia_type: str) -> ad.AnnData:
    """Load expression and metadata from a compendia directory."""
    exp_path = dir / "expression.tsv.gz"
    meta_path = dir / "metadata.tsv.gz"

    exp = pd.read_csv(exp_path, sep="\t", index_col=0).T
    meta = pd.read_csv(meta_path, sep="\t", index_col=0)
    meta["compendia_type"] = compendia_type

    meta = meta.reindex(exp.index)

    return ad.AnnData(X=exp.values, obs=meta, var=pd.DataFrame(index=exp.columns))


def get_disease_counts(adata: ad.AnnData) -> pd.Series:
    """Get count of samples per disease."""
    return adata.obs['disease'].value_counts()


def sample_matching_disease_counts(
    adata: ad.AnnData,
    target_counts: pd.Series,
    disease_col: str = 'disease',
    random_state: int = 42
) -> ad.AnnData:
    """
    Sample from adata to match target disease counts.
    
    Parameters
    ----------
    adata : AnnData
        Source dataset to sample from (e.g., polyA)
    target_counts : pd.Series
        Target counts per disease (e.g., from riboD)
    disease_col : str
        Column name containing disease labels
    random_state : int
        Random seed for reproducibility
    
    Returns
    -------
    AnnData
        Subsetted AnnData with matched disease counts
    """
    rng = np.random.default_rng(random_state)
    selected_indices = []
    
    for disease, target_n in target_counts.items():
        # Get all samples for this disease
        disease_mask = adata.obs[disease_col] == disease
        disease_indices = adata.obs.index[disease_mask]
        
        available_n = len(disease_indices)
        
        if available_n == 0:
            print(f"Warning: No samples found for disease '{disease}' in source dataset")
            continue
        
        if available_n < target_n:
            print(f"Warning: Only {available_n} samples available for '{disease}', "
                  f"but {target_n} requested. Using all available.")
            sampled = disease_indices.tolist()
        else:
            # Randomly sample target_n samples
            sampled = rng.choice(disease_indices, size=target_n, replace=False).tolist()
        
        selected_indices.extend(sampled)
    
    # Subset adata to selected samples
    return adata[selected_indices].copy()


def main():
    print("Loading polyA compendia...")
    polyA_adata = generate_anndata_from_compendia_dir(
        Path("data/0.0.0/Tumor_Compendium_25.01_PolyA_01_2025"), "polyA"
    )
    
    print("Loading riboD compendia...")
    riboD_adata = generate_anndata_from_compendia_dir(
        Path("data/0.0.0/Tumor_Compendium_25.01_RiboD_01_2025"), "riboD"
    )
    
    print("\nRiboD disease counts:")
    riboD_counts = get_disease_counts(riboD_adata)
    print(riboD_counts)
    
    print(f"\nTotal riboD samples: {riboD_adata.n_obs}")
    print(f"Total polyA samples: {polyA_adata.n_obs}")
    
    riboD_disease_counts = get_disease_counts(riboD_adata)
    riboD_disease_counts.to_csv("riboD_disease_counts.tsv", sep="\t")

    riboD_adata = None  # free memory

    print("\nSampling polyA to match riboD disease counts...")
    polyA_matched = sample_matching_disease_counts(
        polyA_adata,
        riboD_counts,
        random_state=42
    )
    
    polyA_matched_disease_counts = get_disease_counts(polyA_matched)

    print("\nPolyA matched disease counts:")
    print(polyA_matched_disease_counts)
    polyA_matched_disease_counts.to_csv("polyA_matched_disease_counts.tsv", sep="\t")
    print(f"Total polyA matched samples: {polyA_matched.n_obs}")
    
    polyA_adata = None  # free memory

    sc.pp.neighbors(polyA_matched, use_rep="X", random_state=42)
    sc.tl.umap(polyA_matched, random_state=42)

    polyA_matched.X = None  # free memory
    polyA_matched.obsp = None  # free memory

    output_path = Path("processed") / "matched_polyA_riboD" / "merged_compendia.h5ad"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    polyA_matched.write_h5ad(output_path)


if __name__ == "__main__":
    main()