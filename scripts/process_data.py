import argparse
from pathlib import Path
import lib_prep_tools
from lib_prep_tools.process import CompendiaListConfig, load_config, generate_hdf5_anndata

DATA_DIR = Path.cwd() / 'data' / str(lib_prep_tools.__version__)
PROCESSED_DIR = Path.cwd() / 'processed'


def parse_args():
    parser = argparse.ArgumentParser(description="Process and merge compendia datasets based on a configuration file.")
    parser.add_argument('--config', type=Path, required=True, help='Path to the process configuration JSON file.')
    args = parser.parse_args()
    return args.config

def main():
    config_path = parse_args()
    process_list_model = load_config(config_path)
    generate_hdf5_anndata(process_list_model, DATA_DIR, PROCESSED_DIR / 'merged_compendia.h5ad')

    # Further processing logic would go here
    pass

if __name__ == "__main__":
    main()