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
    web_endpoint,
    method
)

from . import llm
from . import config
from . import ingest
from . import query
from . import prompts

logger = config.get_logger(__name__)
volume = SharedVolume().persist("chroma-cache-vol")

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
)

stub = Stub(
  "realm-demo",
  image=image,
  secrets=[Secret.from_name("pawan-api")]
)

# for faster cold start times
@stub.cls(
  shared_volumes={config.CACHE_DIR: volume}, 
  gpu="T4",
  container_idle_timeout=600,
  timeout=10000
)
class Embbedding:
  def __enter__(self):
    # from InstructorEmbedding import INSTRUCTOR
    from langchain.embeddings import HuggingFaceInstructEmbeddings
  
    self.embeddings = HuggingFaceInstructEmbeddings(
      model_name="hkunlp/instructor-xl",
      model_kwargs={"device": "cuda"},
      # model_kwargs={"device": "cpu"},
      cache_folder=str(config.MODAL_DIR),
    )
  
  @method()
  def runQuery(self, query_text, search_kwargs={}):
    return query.glide_run(self.embeddings, query_text, search_kwargs)
  
  @method()
  def runIngest(self, texts, chroma_path):
    ingest.glide_run(self.embeddings, texts, chroma_path)

def demo_print(text):
  big_str = f"""
***********************
{text}
***********************  
"""
  print(big_str)
  
def construct_query(llm, query_text, verbose=False):
  # builds a structured query from question
  from langchain.chains.query_constructor.ir import StructuredQuery, Visitor
  from langchain.retrievers.self_query.chroma import ChromaTranslator
  from langchain.chains.query_constructor.base import load_query_constructor_chain
  from langchain.retrievers.self_query.base import SelfQueryRetriever
  from typing import cast

  structured_query_translator: Visitor = ChromaTranslator()
  chain_kwargs = {
      "allowed_comparators": structured_query_translator.allowed_comparators,
      "allowed_operators": structured_query_translator.allowed_operators,
  }

  # setup LLM chain to parse query into a structured query for Chroma
  # referenced from "from langchain.retrievers.self_query.base import SelfQueryRetriever"
  # but removed the part that actually runs the query 
  llm_chain = load_query_constructor_chain(
    llm, config.GLIDE_DOC_DESCRIPTION, config.GLIDE_METADATA_INFO, **chain_kwargs
  )

  inputs = llm_chain.prep_inputs(query_text)
  structured_query = cast(
      StructuredQuery, llm_chain.predict_and_parse(callbacks=None, **inputs)
  )

  if verbose:
    new_query_string = f"Structured query: {structured_query.query}"
    if structured_query.filter is not None:
      new_query_string += "\n    Filters:\n"
      for f in structured_query.filter:
        new_query_string += f"        {f}\n"
    demo_print(new_query_string)

  return structured_query_translator.visit_structured_query(structured_query=structured_query)


# run ingest flag to ingest
# otherwise run query to sample
@stub.local_entrypoint()
def main():
  from typing import List
  from langchain.schema import Document
  import traceback

  DO_INGEST = False

  # create llm instance
  pawan_llm = llm.CustomLLM()
  
  logger.info("create embedding instance...")
  embed = Embbedding()


  if DO_INGEST:
    file_path = "./GLIDE/"
    logger.info(f"ingesting from {file_path}...")

    docs = ingest.glide_load_documents(file_path)
    
    logger.info(f"ingesting {len(docs)} documents...")
    embed.runIngest.call(docs, chroma_path=str(config.CHROMA_DIR))

    logger.info("ingestion complete!")
    return
  
  # avoid cold start 
  embed.runQuery.call("Hello World")

  # query_text = input("Enter a question: ")

  logger.info("begin evaluation...")

  def generate_answer(question):
    print("\n1. Get question from user...")
    demo_print(f"Question: {query_text}")
    # Preprocess the input into a structured query
    print(f"2. Construct structured query using ChatGPT LLM proxy...")
    new_query, new_kwargs = construct_query(pawan_llm, question, verbose=True)
    
    # pass structured query to modal embedding
    print(f"3. Retrieving documents from vectorDB...")
    documents: List[Document] = embed.runQuery.call(new_query, new_kwargs)
    demo_print(f"Retrieval: Retrieved {len(documents)} documents from vectorDB")
    
    # build a new prompt
    print(f"4. Concatenate everything into a big prompt...")
    prompt = prompts.glide_construct_prompt(question, documents)
    # demo_print(f"Final Propmt:\n\n{prompts.glide_constrct_demo_prompt(question, documents)}\n")
    # logger.info(f"Final Prompt:\n\n {prompt}")

    # run the prompt
    print(f"5. Pass big prompt into ChatGPT LLM proxy...")
    answer = pawan_llm(prompt)
    # logger.info(f"Final Response: {answer}")
    demo_print(f"Final answer:\n\n{answer}\n")

  # the main demo loop
  query_text = ""
  while True:
    try:
      query_text = input("Enter a question: ") #  list out different components that make up the U-net architecture for diffusion models
      if query_text == "exit":
        break
      generate_answer(query_text)
    except Exception as e:
      logger.error(traceback.format_exc())
      continue

# list out different components that make up the U-net architecture for diffusion models
# Why does the GLIDE model need attention layers if it already uses text-conditioned guided diffusion?
# What are some potential reasons that classifier free guidance work so much better than classifier guided diffusion?

  # query_text = input("Enter a question: ") # Why does the GLIDE model need attention layers if it already uses text-conditioned guided diffusion?
  # generate_answer(query_text)

  # query_text = input("Enter a question: ") # What are some potential reasons that classifier free guidance work so much better than classifier guided diffusion?
  # generate_answer(query_text)


  # try:
  #   # Preprocess the input into a structured query
  #   # add phrase to filter for the specific paper
  #   temp_q = INPUT_OBJ["question"].split("?")[0]
  #   temp_prompt = f"In the context of the research paper titled \"{INPUT_OBJ['title']}\", {temp_q}?"
  #   new_query, new_kwargs = construct_query(pawan_llm, temp_prompt, verbose=False)
    
  #   # pass structured query to modal embedding
  #   documents: List[Document] = embed.runQuery.call(new_query, new_kwargs)
  #   # TODO: do this if we can rank the evidence
  #   pawan_llm.set_evidence(documents)
  #   # logger.info(f"Retrieved {len(documents)} documents")

  #   # Build a new prompt
  #   examples = prompts.qasper_construct_examples(dev_dataset, config.K_SHOT)
  #   prompt = prompts.qasper_construct_prompt(INPUT_OBJ["question"], documents, examples, config.K_SHOT)
  #   # logger.info(f"Final Prompt:\n\n {prompt}")

  #   # query LLM
  #   answer = pawan_llm(prompt)
  #   # logger.info(f"Final Response: {answer}")

  # except Exception as e:
  #   logger.error(f"Error: {e}")
  #   logger.error(traceback.format_exc(limit=2))



# TODO: Albation: without evidence, without explanation, without query structure