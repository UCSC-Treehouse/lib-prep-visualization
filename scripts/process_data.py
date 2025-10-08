import argparse
from pathlib import Path
from lib_prep_tools.process import CompendiaListConfig, load_config

def parse_args():
    parser = argparse.ArgumentParser(description="Process and merge compendia datasets based on a configuration file.")
    parser.add_argument('--config', type=Path, required=True, help='Path to the process configuration JSON file.')
    args = parser.parse_args()
    return args.config

def main():
    config_path = parse_args()
    process_list_model = load_config(config_path)
    print(process_list_model)
    # Further processing logic would go here
    pass

if __name__ == "__main__":
    main()