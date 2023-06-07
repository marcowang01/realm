# packages installed at wherever env the modal binary is running
from langchain.docstore.document import Document
from typing import List

from . import config
logger = config.get_logger(__name__)


def load_single_document(file_path: str) -> Document:
    from langchain.document_loaders import TextLoader, PDFMinerLoader, CSVLoader
    # Loads a single document from a file path
    if file_path.endswith(".txt"):
        loader = TextLoader(file_path, encoding="utf8")
    elif file_path.endswith(".pdf"):
        loader = PDFMinerLoader(file_path)
    elif file_path.endswith(".csv"):
        loader = CSVLoader(file_path)
    return loader.load()[0]


def load_documents(path: str) -> List[Document]:
    # returns a list of Documents to initialize a Chroma database
    import os
    import json
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = []
    # Loads all documents from source documents directory
    if os.path.isdir(path):
      all_files = os.listdir(path)
      docs = [load_single_document(f"{path}/{file_path}") for file_path in all_files if file_path[-4:] in ['.txt', '.pdf', '.csv'] ]
      # TODO: use arxiv retriever to get metadata: title, date, arxiv_id
      texts = text_splitter.split_documents(docs)
    # special case for qasper papers. format: [{"full_text": "text", "metadata": {...}}, {...}, ...]
    elif path.endswith("papers.json"):
      # print the full current working directory
      logger.info(f"Loading papers from {path}...")
      data = json.load(open(path))
      for paper in data:
        chunks = text_splitter.split_text(paper['full_text'])
        texts += [Document(page_content=chunk, metadata=paper['metadata']) for chunk in chunks]
        # break # for testing, embed only the first paper

    return texts

# create and insert embeddings into Chroma database
def run(texts: List[Document]):
  from langchain.vectorstores import Chroma
  from langchain.embeddings import HuggingFaceInstructEmbeddings
  from chromadb.config import Settings
  from InstructorEmbedding import INSTRUCTOR
  import torch
  import sentence_transformers

  # Create embeddings
  embeddings = HuggingFaceInstructEmbeddings(
    model_name="hkunlp/instructor-xl",
    model_kwargs={"device": "cuda"},
    # model_kwargs={"device": "cpu"},
    cache_folder=str(config.MODAL_DIR),
  )
  settings = Settings(
      chroma_db_impl='duckdb+parquet',
      persist_directory=str(config.CHROMA_DIR),
      anonymized_telemetry=False
  )
  
  logger.info("Creating Chroma database...")
  db = Chroma.from_documents(texts, embeddings, persist_directory=str(config.CHROMA_DIR), client_settings=settings)
  db.persist()
  db = None
  logger.info("Created Chroma database.")

def deleteDB():
  from langchain.vectorstores import Chroma
  from langchain.embeddings import HuggingFaceInstructEmbeddings

  embeddings = HuggingFaceInstructEmbeddings(
    model_name="hkunlp/instructor-xl",
    model_kwargs={"device": "cuda"},
    cache_folder=str(config.MODAL_DIR),
  )

  db = Chroma(persist_directory=str(config.CHROMA_DIR), embedding_function=embeddings)
  db.delete_collection()
  logger.info("Deleted Chroma database.")
