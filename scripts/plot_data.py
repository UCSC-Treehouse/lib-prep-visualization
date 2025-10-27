import argparse
from pathlib import Path
from lib_prep_tools.plot import load_plot_config, load_scanpy_adata, validate_color_by, plot_umap
import logging.config

FIGURE_DIR = Path.cwd() / 'figures'
PLOTTING_LOG = FIGURE_DIR / 'plotting.log'

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(levelname)s: %(message)s"
        },
        "detailed": {
            "format": "[%(levelname)s|%(module)s|%(lineno)d] %(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z"  # ISO 8601 with timezone
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": str(PLOTTING_LOG),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 3
        }
    },
    "loggers": {
        "root": {"level": "DEBUG", "handlers": ["stdout", "file"]},
    }
}

def parse_args():
    parser = argparse.ArgumentParser(description="Plot processed compendia data.")
    parser.add_argument('--config', type=Path, required=True, help='Path to the processed .h5ad file.')
    args = parser.parse_args()
    return args.config

def main():
    config_path = parse_args()
    FIGURE_DIR.mkdir(exist_ok=True)
    PLOTTING_LOG.touch(exist_ok=True)
    logging.config.dictConfig(config=logging_config)
    plot_config = load_plot_config(config_path)
    adata = load_scanpy_adata(Path(plot_config.src_adata_path))
    fig = plot_umap(adata, plot_config)
    fig.savefig(FIGURE_DIR / f"{plot_config.plot_title.replace(' ', '_')}.png", dpi=1200)

if __name__ == "__main__":
    main()