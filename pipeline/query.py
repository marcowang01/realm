from langchain.docstore.document import Document

from . import config
logger = config.get_logger(__name__)
 

def run(embeddings, query_text: str, search_kwargs: dict = {}):
  from langchain.vectorstores import Chroma
  from langchain.embeddings import HuggingFaceInstructEmbeddings
  from chromadb.config import Settings
  from InstructorEmbedding import INSTRUCTOR
  from langchain.chains import RetrievalQA
  from langchain.prompts import PromptTemplate
  from langchain.retrievers.self_query.base import SelfQueryRetriever

  # Create embeddings
  # embeddings = HuggingFaceInstructEmbeddings(
  #   model_name="hkunlp/instructor-xl",
  #   model_kwargs={"device": "cuda"},
  #   # model_kwargs={"device": "cpu"},
  #   cache_folder=str(config.MODAL_DIR),
  # )
  settings = Settings(
    chroma_db_impl='duckdb+parquet',
    persist_directory=str(config.CHROMA_DIR),
    anonymized_telemetry=False
  )

  db = Chroma(persist_directory=str(config.CHROMA_DIR), embedding_function=embeddings, client_settings=settings)

  search_kwargs = {**search_kwargs, "k": config.K_DOCS}

  retriever = db.as_retriever(search_kwargs=search_kwargs)

  docs = retriever.get_relevant_documents(query_text)

  return docs

  # prompt_context = "Context for the question:\n\n"

  # for doc in docs:
  #   prompt_context += f"{doc.page_content}\n\n"

  # return prompt_context