import dataclasses
import logging
import pathlib

def get_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(levelname)s: %(asctime)s: %(name)s  %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False  # Prevent the modal client from double-logging.
    return logger


CACHE_DIR = "/cache"

# Location of chroma persist directory.
CHROMA_DIR = pathlib.Path(CACHE_DIR, "chroma")
INDEX_DIR = pathlib.Path(CHROMA_DIR, "index")
S3_KEY = "chroma.zip"
ZIP_FILE = pathlib.Path(CACHE_DIR, S3_KEY)

# Location of web frontend assets.
ASSETS_PATH = pathlib.Path(__file__).parent / "frontend" / "dist"

# chunks of instructions to send to openai
CHUNK_SIZE = 1000