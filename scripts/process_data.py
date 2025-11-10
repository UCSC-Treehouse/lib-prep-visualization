import argparse
from pathlib import Path
import lib_prep_tools
from lib_prep_tools.process import CompendiaListConfig, load_config, generate_h5ad_anndata
import logging.config

DATA_DIR = Path.cwd() / 'data' / str(lib_prep_tools.__version__)
PROCESSED_DIR = Path.cwd() / 'processed'
PROCESS_LOG = PROCESSED_DIR / 'process.log'

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
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": str(PROCESS_LOG),
            "mode": "w"
        }
    },
    "loggers": {
        "root": {"level": "DEBUG", "handlers": ["stdout", "file"]},
    }
}


def parse_args():
    parser = argparse.ArgumentParser(description="Process and merge compendia datasets based on a configuration file.")
    parser.add_argument('--config', type=Path, required=True, help='Path to the process configuration JSON file.')
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=DATA_DIR,
        help=(
            "Path to the directory containing downloaded data. "
            "The directory must match the output formatting of the download_data script."
        ),
    )
    args = parser.parse_args()
    return args.config, args.data_dir

def main():
    config_path, data_dir = parse_args()
    PROCESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    PROCESS_LOG.touch(exist_ok=True)
    logging.config.dictConfig(logging_config)
    process_list_model = load_config(config_path)
    output_dir = PROCESSED_DIR / process_list_model.out_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    generate_h5ad_anndata(process_list_model, data_dir, output_dir / 'merged_compendia.h5ad')

    # Further processing logic would go here
    pass

if __name__ == "__main__":
    main()