import argparse
from lib_prep_tools import __version__
from lib_prep_tools.download import load_config
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Download compendia datasets based on a configuration file.")
    parser.add_argument('--config', type=Path, required=True, help='Path to the download configuration JSON file.')
    args = parser.parse_args()
    return args.config

def main():
    config_path = parse_args()
    download_list_model = load_config(config_path)
    print(download_list_model)

if __name__ == "__main__":
    main()