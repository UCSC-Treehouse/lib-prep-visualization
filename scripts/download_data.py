import argparse
import lib_prep_tools
from lib_prep_tools.download import load_config, load_manifest, DownloadListConfig, download_compendia
from pathlib import Path

DATA_DIR = Path.cwd() / 'data' / str(lib_prep_tools.__version__)
MANIFEST_PATH = DATA_DIR / 'download_manifest.json'

def parse_args():
    parser = argparse.ArgumentParser(description="Download compendia datasets based on a configuration file.")
    parser.add_argument('--config', type=Path, required=True, help='Path to the download configuration JSON file.')
    args = parser.parse_args()
    return args.config

def main():
    config_path = parse_args()
    download_list_model = load_config(config_path)
    manifest_model = load_manifest(MANIFEST_PATH)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    download_manifest = download_compendia(download_list_model, manifest_model, DATA_DIR, str(lib_prep_tools.__version__))
    with open(MANIFEST_PATH, 'w') as f:
        f.write(download_manifest.model_dump_json(indent=4))

if __name__ == "__main__":
    main()