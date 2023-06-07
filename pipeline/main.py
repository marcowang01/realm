import dataclasses
import datetime
import json
import pathlib
import os
from typing import Iterator, Tuple

from modal import (
    Dict,
    Image,
    Mount,
    Period,
    Secret,
    SharedVolume,
    Stub,
    asgi_app,
    gpu,
    web_endpoint
)

from . import config
from . import ingest
from . import query

logger = config.get_logger(__name__)
volume = SharedVolume().persist("chroma-cache-vol")

def download_model():
  from InstructorEmbedding import INSTRUCTOR
  from langchain.embeddings import HuggingFaceInstructEmbeddings

  # Create embeddings
  embeddings = HuggingFaceInstructEmbeddings(
    model_name="hkunlp/instructor-xl",
    # model_kwargs={"device": "cuda"},
    model_kwargs={"device": "cpu"},
    cache_folder=str(config.MODAL_DIR),
  )

image = (
  Image.debian_slim()
  .pip_install(
    "openai",
    "boto3",
    "langchain",
    "chromadb",
    "llama-cpp-python",
    "urllib3",
    "pdfminer.six",
    "InstructorEmbedding",
    "sentence-transformers",
    "faiss-cpu",
    "huggingface_hub",
    "transformers",
    "protobuf",
    "accelerate",
    "bitsandbytes",
    "click"
  )
  .run_function(download_model)
)

stub = Stub(
  "realm",
  image=image,
  secrets=[Secret.from_name("pawan-api")]
)

# handler for running the ingest function
@stub.function(
    shared_volumes={config.CACHE_DIR: volume}, 
    gpu="a100-20g",
    timeout=10000,
    allow_cross_region_volumes=True,
  )
def runIngestion(texts):
  # ingest.deleteDB()
  ingest.run(texts)


@stub.function(
    shared_volumes={config.CACHE_DIR: volume}, 
    gpu="T4",
    timeout=5000,
  )
def runQuery(query_text):
  return query.run(query_text)
  

# run ingest flag to ingest
# otherwise run query to sample
@stub.local_entrypoint()
def main():
  # FIXME: This is a hack, requires user to install langchain globally
  # potential fix: can just use modal bin in venv
  # or use web endpoints for everything is better eventually
  INGEST_PATH = "./qasper/test-papers.json"
  DO_INGESTION = True
  DO_INGESTION = False

  # if ingest_path is set, run ingestion base on path
  if DO_INGESTION:
    texts = ingest.load_documents(INGEST_PATH)
    logger.info(f"Loaded {len(texts)} chunks from {INGEST_PATH}")
    runIngestion.call(texts)
  else:
    logger.info("Running query")
    query_text = "What is a seed lexicon?"
    result = runQuery.call(query_text)
    logger.info(f"Result:\n{result}")

