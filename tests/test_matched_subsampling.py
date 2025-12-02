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

metadata_4 = pd.DataFrame({
    "sample_id": ["S13", "S14", "S15", "S16"],
    "disease": ["D", "D", "E", "E"],
})

metadata_5 = pd.DataFrame({
    "sample_id": ["S17", "S18", "S19", "S20"],
    "disease": ["A", "B", "B", "B"],
})

metadata_7 = pd.DataFrame({
    "sample_id": ["S21", "S22", "S23", "S24"],
    "age": [1, 2, 3, 4],
})


def test_two_compendia_matching_entries():
    """
    Test the simplest case where both compendia have the same disease entries.
    """
    meta_df_dict = {
        "compendia_1": metadata_1,
        "compendia_2": metadata_2,
    }
    result = compute_min_sample_counts(meta_df_dict, "disease")
    expected = {"A": 2, "B": 2}
    assert result == expected

def test_two_compendia_with_one_unique_entry():
    """
    Test when one compendia has a unique disease entry not found in the other.
    """
    meta_df_dict = {
        "compendia_1": metadata_1,
        "compendia_3": metadata_3,
    }
    result = compute_min_sample_counts(meta_df_dict, "disease")
    expected = {"A": 1, "B": 2}
    assert result == expected

def test_two_compendia_no_matching_entries():
    """
    Test when both compendia have completely different disease entries.
    """
    meta_df_dict = {
        "compendia_1": metadata_1,
        "compendia_4": metadata_4,
    }
    result = compute_min_sample_counts(meta_df_dict, "disease")
    expected = {}
    assert result == expected

def test_three_compendia_matching_entries():
    """
    Test with three compendia having some overlapping disease entries. 'A' only appears once in metadata_5.
    """
    meta_df_dict = {
        "compendia_1": metadata_1,
        "compendia_2": metadata_2,
        "compendia_5": metadata_5,
    }
    result = compute_min_sample_counts(meta_df_dict, "disease")
    expected = {"A": 1, "B": 2}
    assert result == expected

def test_three_compendia_one_unique_entry():
    """
    Test with three compendia where one has a unique disease entry not found in the others. 'C' only appears in metadata_3.
    """
    meta_df_dict = {
        "compendia_1": metadata_1,
        "compendia_2": metadata_2,
        "compendia_3": metadata_3,
    }
    result = compute_min_sample_counts(meta_df_dict, "disease")
    expected = {"A": 1, "B": 2}
    assert result == expected

def test_three_compendia_one_unique_compendia():
    """
    Test with three compendia where one has completely different disease entries. Result should be empty.
    """
    meta_df_dict = {
        "compendia_1": metadata_1,
        "compendia_2": metadata_2,
        "compendia_4": metadata_4,
    }
    result = compute_min_sample_counts(meta_df_dict, "disease")
    expected = {}
    assert result == expected