import argparse
from pathlib import Path
from lib_prep_tools.plot import load_plot_config, load_scanpy_adata, validate_meta_variable, plot_umap

FIGURE_DIR = Path.cwd() / 'figures'

def parse_args():
    parser = argparse.ArgumentParser(description="Plot processed compendia data.")
    parser.add_argument('--config', type=Path, required=True, help='Path to the processed .h5ad file.')
    args = parser.parse_args()
    return args.config

def main():
    config_path = parse_args()
    plot_config = load_plot_config(config_path)
    adata = load_scanpy_adata(Path(plot_config.src_adata_path))
    validate_meta_variable(adata, plot_config)
    FIGURE_DIR.mkdir(exist_ok=True)
    fig = plot_umap(adata, plot_config)
    fig.savefig(FIGURE_DIR / f"{plot_config.plot_title.replace(' ', '_')}.png", dpi=1200)

if __name__ == "__main__":
    main()