# packages installed at wherever env the modal binary is running
from langchain.docstore.document import Document
from typing import List

from . import config
logger = config.get_logger(__name__)


def glide_get_metadata(arxiv_id: str) -> dict:
  from datetime import datetime
  import requests
  import feedparser

  base_url = 'http://export.arxiv.org/api/query?'
  query = 'id_list={}'.format(arxiv_id)
  response = requests.get(base_url + query)
  feed = feedparser.parse(response.content)
    
  if len(feed.entries) > 0:
    entry = feed.entries[0]
    return {
      "title": entry.title,
      # translate to unix timestamp
      "date": int(datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ").timestamp()),
      "arxiv_id": arxiv_id
    }
  else:
    raise ValueError("No paper found with the given arXiv id.")

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


def glide_load_documents(path: str) -> List[Document]:
  import os
  from langchain.schema import Document
  from langchain.text_splitter import RecursiveCharacterTextSplitter
  # bigger window for more context and more abstraction
  text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
  docs = []
  
  all_files = os.listdir(path)
  for file_path in all_files:
    arxiv_id = file_path[:-4]
    document = load_single_document(f"{path}/{file_path}")
    chunks = text_splitter.split_text(document.page_content)
    metadata = glide_get_metadata(arxiv_id)
    docs += [Document(page_content=chunk, metadata=metadata) for chunk in chunks]

  return docs


# when have time change this to qasper only
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
def run(embeddings, texts: List[Document], chroma_path):
  from langchain.vectorstores import Chroma
  from chromadb.config import Settings

  settings = Settings(
      chroma_db_impl='duckdb+parquet',
      persist_directory=str(config.CHROMA_DIR),
      anonymized_telemetry=False
  )
  
  logger.info("Creating Chroma database...")
  db = Chroma.from_documents(texts, embeddings, persist_directory=str(config.CHROMA_DIR), client_settings=settings)
  db.persist()
  db.persist()
  db = None
  logger.info("Created Chroma database.")

def glide_run(embeddings, texts: List[Document]):
  from langchain.vectorstores import Chroma
  from chromadb.config import Settings

  settings = Settings(
      chroma_db_impl='duckdb+parquet',
      persist_directory=str(config.GLIDE_DIR),
      anonymized_telemetry=False
  )
  
  logger.info("Creating Chroma database...")
  db = Chroma.from_documents(texts, embeddings, persist_directory=str(config.GLIDE_DIR), client_settings=settings)
  db.persist()
  db.persist()
  db = None
  logger.info("Created Chroma database.")

# def deleteDB(embeddings, chroma_path=str(config.CHROMA_DIR)):
#   from langchain.vectorstores import Chroma

#   db = Chroma(persist_directory=chroma_path, embedding_function=embeddings)
#   db.delete_collection()
#   logger.info("Deleted Chroma database.")
