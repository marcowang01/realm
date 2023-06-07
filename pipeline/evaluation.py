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
  "realm-evaluation",
  image=image,
  secrets=[Secret.from_name("pawan-api")]
)

# for faster cold start times
@stub.cls(
  shared_volumes={config.CACHE_DIR: volume}, 
  gpu="T4",
  container_idle_timeout=600,
  timeout=5000
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
    return query.run(self.embeddings, query_text, search_kwargs)

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
    llm, config.QASPER_DOC_DESCRIPTION, config.QASPER_METADATA_INFO, **chain_kwargs
  )

  inputs = llm_chain.prep_inputs(query_text)
  structured_query = cast(
      StructuredQuery, llm_chain.predict_and_parse(callbacks=None, **inputs)
  )

  if verbose:
    logger.info(f"\n    Query: {structured_query.query}")
    filter_str = "\n    Filters:\n"
    for f in structured_query.filter:
      filter_str += f"        {f}\n"
    logger.info(filter_str)

  return structured_query_translator.visit_structured_query(structured_query=structured_query)


# run ingest flag to ingest
# otherwise run query to sample
@stub.local_entrypoint()
def main():
  from typing import List
  from langchain.schema import Document
  import traceback

  # INPUT_OBJ = {
  #   "question_id": "397a1e851aab41c455c2b284f5e4947500d797f0",
  #   "title": "End-to-End Trainable Non-Collaborative Dialog System",
  #   "arxiv_id": "1911.10742",
  #   "question": "How big is the ANTISCAM dataset?",
  #   # "answer": "220 human-human dialogs",
  # }

  # INPUT_OBJ = {
  #   "question_id": "079ca5810060e1cdc12b5935d8c248492f0478b9",
  #   "title": "Italian Event Detection Goes Deep Learning",
  #   "arxiv_id": "1810.02229",
  #   "question": "Can the model be extended to other languages?",
  #   # "answer": "unasnwerable",
  # }

  # total number of questions to sample
  TRIALS = 500
  START = 0

  # create llm instance
  pawan_llm = llm.CustomLLM()

  logger.info("load in datasets to local memory...")
  # load in the dev set to generate few-shot examples
  dev_path = "qasper/qasper-dev-v0.3.json"
  dev_dataset = json.load(open(dev_path))
  # load in the test set to run the actual evaluation
  test_path = "qasper/qasper-test-v0.3.json"
  test_dataset = json.load(open(test_path))
  
  logger.info("load in embedding model to remote gpu memory...")
  embed = Embbedding()
  # avoid cold start 
  # embed.__enter__()
  embed.runQuery.call("Hello World")

  logger.info("begin evaluation...")

  count = 0
  for key, value in test_dataset.items():
    paper = value
    if count >= TRIALS:
      break
    for qa in paper["qas"]:
      if count >= TRIALS:
        break
      if count <= START:
        count += 1
        continue
      
      INPUT_OBJ = {
        "question_id": qa["question_id"],
        "title": paper["title"],
        "question": qa["question"],
        "arxiv_id": key,
      }
      logger.info(f"Evaluating question {count + 1}/{TRIALS}")
      try:
        # Preprocess the input into a structured query
        # add phrase to filter for the specific paper
        temp_q = INPUT_OBJ["question"].split("?")[0]
        temp_prompt = f"In the context of the research paper titled \"{INPUT_OBJ['title']}\", {temp_q}?"
        new_query, new_kwargs = construct_query(pawan_llm, temp_prompt, verbose=False)
        
        # pass structured query to modal embedding
        documents: List[Document] = embed.runQuery.call(new_query, new_kwargs)
        # TODO: do this if we can rank the evidence
        pawan_llm.set_evidence(documents)
        # logger.info(f"Retrieved {len(documents)} documents")

        # Build a new prompt
        examples = prompts.qasper_construct_examples(dev_dataset, config.K_SHOT)
        prompt = prompts.qasper_construct_prompt(INPUT_OBJ["question"], documents, examples, config.K_SHOT)
        # logger.info(f"Final Prompt:\n\n {prompt}")

        # query LLM
        answer = pawan_llm(prompt)
        # logger.info(f"Final Response: {answer}")

        # save to json
        result_path = f"./out/pipeline_result.jsonl"
        pawan_llm.qasper_export_jsonl(INPUT_OBJ["question_id"], result_path)
        logger.info(f"Saved answer {count + 1}/{TRIALS}")
        count += 1
      except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc(limit=2))
        continue



# TODO: Albation: without evidence, without explanation, without query structure