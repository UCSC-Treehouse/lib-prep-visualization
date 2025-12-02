import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from matched_subsampling import compute_min_sample_counts


def test_two_compendia_matching_entries():
    pass