import argparse
from pathlib import Path
from lib_prep_tools.plot import load_plot_config

def parse_args():
    parser = argparse.ArgumentParser(description="Plot processed compendia data.")
    parser.add_argument('--config', type=Path, required=True, help='Path to the processed .h5ad file.')
    args = parser.parse_args()
    return args.config

def main():
    config_path = parse_args()
    plot_config = load_plot_config(config_path)
    print(plot_config)

if __name__ == "__main__":
    main()