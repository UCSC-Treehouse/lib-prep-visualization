import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from matched_subsampling import compute_min_sample_counts


metadata_1 = pd.DataFrame({
    "sample_id": ["S1", "S2", "S3", "S4"],
    "disease": ["A", "A", "B", "B"],
})

metadata_2 = pd.DataFrame({
    "sample_id": ["S5", "S6", "S7", "S8"],
    "disease": ["A", "A", "B", "B"],
})

metadata_3 = pd.DataFrame({
    "sample_id": ["S9", "S10", "S11", "S12"],
    "disease": ["A", "B", "B", "C"],
})


def test_two_compendia_matching_entries():
    meta_df_dict = {
        "compendia_1": metadata_1,
        "compendia_2": metadata_2,
    }
    result = compute_min_sample_counts(meta_df_dict, "disease")
    expected = {
        "A": 2,
        "B": 2,
    }
    assert result == expected