import argparse
from pathlib import Path
import lib_prep_tools
from lib_prep_tools.process import CompendiaListConfig, load_config, validate_compendia_dirs

DATA_DIR = Path.cwd() / 'data' / str(lib_prep_tools.__version__)

def parse_args():
    parser = argparse.ArgumentParser(description="Process and merge compendia datasets based on a configuration file.")
    parser.add_argument('--config', type=Path, required=True, help='Path to the process configuration JSON file.')
    args = parser.parse_args()
    return args.config

def main():
    config_path = parse_args()
    process_list_model = load_config(config_path)
    if not validate_compendia_dirs(process_list_model, DATA_DIR):
        print("One or more compendia directories are missing.")
        return
    # Further processing logic would go here
    pass

if __name__ == "__main__":
    main()