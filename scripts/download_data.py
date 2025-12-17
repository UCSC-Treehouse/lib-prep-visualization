import argparse
import lib_prep_tools
from lib_prep_tools.download import load_config, load_manifest, DownloadListConfig, download_compendia
from pathlib import Path
import logging.config

DATA_DIR = Path.cwd() / 'data' / str(lib_prep_tools.__version__)
MANIFEST_PATH = DATA_DIR / 'download_manifest.json'
DOWNLOAD_LOG = DATA_DIR / 'download.log'

logger = logging.getLogger("download_data")

# Set up logging configuration. 
# There are two handlers: one for console output and one for a rotating log file that will keep logs for debugging purposes.
# There are two formatters: a simple one for console output and a detailed one for the log file.
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
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(DOWNLOAD_LOG),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 3
        }
    },
    "loggers": {
        "root": {"level": "DEBUG", "handlers": ["stdout", "file"]},
    }
}

def parse_args():
    parser = argparse.ArgumentParser(description="Download compendia datasets based on a configuration file.")
    parser.add_argument('--config', type=Path, required=True, help='Path to the download configuration JSON file.')
    args = parser.parse_args()
    return args.config

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_LOG.touch(exist_ok=True)
    logging.config.dictConfig(config=logging_config)
    config_path = parse_args()
    download_list_model = load_config(config_path)
    manifest_model = load_manifest(MANIFEST_PATH)
    try:
        download_compendia(download_list_model, manifest_model, DATA_DIR, str(lib_prep_tools.__version__))
    finally:
        with open(MANIFEST_PATH, 'w') as f:
            f.write(manifest_model.model_dump_json(indent=4))

if __name__ == "__main__":
    main()