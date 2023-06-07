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
MODAL_DIR = pathlib.Path(CACHE_DIR, "modal") # stores cache of the embedding model
CHROMA_DIR = pathlib.Path(CACHE_DIR, "chroma") # stores persisted chroma db
GLIDE_DIR = pathlib.Path(CACHE_DIR, "glide") # this doesnt rly work
INDEX_DIR = pathlib.Path(CHROMA_DIR, "index") # the actual files containing the embeddings and texts
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
K_SHOT = 6

"""
Config for evaluation on QASPER
"""
QASPER_METADATA_INFO = [
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
QASPER_DOC_DESCRIPTION = "Excerpts from the full text of the research paper."

"""
Config for GLIDE demo
"""
GLIDE_METADATA_INFO = [
    AttributeInfo(
        name="title",
        description="The title of the research paper",
        type="string",
    ),
    AttributeInfo(
        name="date",
        description="The date the paper was published expressed in unix time",
        type="int",
    ),
    AttributeInfo(
        name="arxiv_id",
        description="The unique arxiv id of the paper",
        type="string",
    ),
]
GLIDE_DOC_DESCRIPTION = "Excerpts from the full text of the research paper."