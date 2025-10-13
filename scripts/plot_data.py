import argparse
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Plot processed compendia data.")
    parser.add_argument('--config', type=Path, required=True, help='Path to the processed .h5ad file.')
    args = parser.parse_args()
    return args.config

def main():
    config_path = parse_args()
    print(f"Config path: {config_path}")

if __name__ == "__main__":
    main()