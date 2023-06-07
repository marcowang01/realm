import dataclasses
import logging
import pathlib
from langchain.chains.query_constructor.base import AttributeInfo

"""
General config for the REALM pipeline.
"""
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
MODAL_DIR = pathlib.Path(CACHE_DIR, "modal")
CHROMA_DIR = pathlib.Path(CACHE_DIR, "chroma")
INDEX_DIR = pathlib.Path(CHROMA_DIR, "index")
S3_KEY = "chroma.zip"
ZIP_FILE = pathlib.Path(CACHE_DIR, S3_KEY)

# Location of web frontend assets.
ASSETS_PATH = pathlib.Path(__file__).parent / "frontend" / "dist"

# chunks of instructions to send to openai
CHUNK_SIZE = 1000

PAWAN_API_URL = "https://api.pawan.krd/v1/chat/completions"
PAWAN_API_KEY = "pk-SCfIRSxcfoewLTsUagmpHJMVFwVbPjHDrNeVJAbagnnEjzLD"

# number of documents to retrieve from chroma
K_DOCS = 6

# number of examples to generate for ICL few shot learning
K_SHOT = 8

"""
Config for evaluation on QASPER
"""
METADATA_INFO = [
    AttributeInfo(
        name="title",
        description="The title of the research paper", 
        type="string", 
    ),
    AttributeInfo(
        name="publication_date",
        description="The date the paper was published", 
        type="date", 
    ),
    AttributeInfo(
        name="arxiv_id",
        description="The arxiv id of the paper", 
        type="string", 
    ),
]
DOC_DESCRIPTION = "The full text of the research paper."

