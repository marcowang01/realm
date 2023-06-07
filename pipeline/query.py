from langchain.docstore.document import Document
from typing import Any, List, Mapping, Optional
from enum import Enum
from langchain.llms.base import LLM

from . import config
logger = config.get_logger(__name__)


class CustomLLM(LLM):
  from langchain.callbacks.manager import CallbackManagerForLLMRun
  from langchain.llms.base import LLM


  @property
  def _llm_type(self) -> str:
    return "custom"
  
  def _call(
    self,
    prompt: str,
    stop: Optional[List[str]] = None,
    run_manager: Optional[CallbackManagerForLLMRun] = None,
  ) -> str:
    import os
    import requests
    import json

    if stop is not None:
      raise ValueError("stop kwargs are not permitted.")
    answer = ""

    system_prompt = "You are a model trained on diverse datasets, you have the ability to provide insights on a wide range of topics, including machine learning."
    headers = {
      "Authorization": f"Bearer {os.environ['PAWAN_API_KEY']}",
      "Content-Type": "application/json",
    }
    messages = [
      {
        "role": "system",
        "content": system_prompt
      },
      {
        "role": "user",
        "content": prompt
      }
    ]
    payload = {
      "model": "gpt-3.5-turbo",
      "max_tokens": "256",
      "messages": messages,
    }

    response = requests.post("https://api.pawan.krd/v1/chat/completions", headers=headers, json=payload)
    if response.status_code != 200:
      # try:
      #     error_message = response.json()
      # except ValueError:  # includes simplejson.decoder.JSONDecodeError
      #     error_message = response.text
      raise Exception(f"PawanGPT ERROR: {response.status_code}")
    answer = response.json()['choices'][0]['message']['content']

    self.answer = answer
    return answer
  
  def sample(self, question_id: str) -> List[str]:
    import json
    
    json_data = {}
    json_data = {
      "question_id": question_id,
      "predicted_answer": self.answer,
      "predicted_evidence": ["n/a"],
    }
    return json.dumps(json_data)
 

def run(query_text: str):
  from langchain.vectorstores import Chroma
  from langchain.embeddings import HuggingFaceInstructEmbeddings
  from chromadb.config import Settings
  from InstructorEmbedding import INSTRUCTOR
  from langchain.chains import RetrievalQA
  from langchain.prompts import PromptTemplate
  from langchain.retrievers.self_query.base import SelfQueryRetriever

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

#   prompt_template = """Use the following pieces of context to answer the question at the end.

# {context}

# Question: {question}

# Instructions:
# Please answer directly and concisely without providing additional explanations or context and without any preamble or introduction. 
# If the question cannot be answered based on available information or the paper doesn't provide enough evidence, respond with only the word 'Unanswerable'.
# If the paper does not provide the necesary evidence or information related to the question, please respond only with the word 'Unanswerable'.
# If the question can be answered using 'Yes' or 'No', please respond with only the word 'Yes' or 'No'.
# If the question can be answered using a number, please respond with only the number.
# If the question can be asnwered using a term or a list of terms, please respond with only the term or list of terms."""

  # PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
  # chain_type_kwargs = {"prompt": PROMPT}

  db = Chroma(persist_directory=str(config.CHROMA_DIR), embedding_function=embeddings, client_settings=settings)
  retriever = db.as_retriever(search_kwargs={"k": 5})

  docs = retriever.get_relevant_documents(query_text)

  prompt_context = "Context for the question:\n\n"

  for doc in docs:
    prompt_context += f"{doc.page_content}\n\n"

  # llm = CustomLLM()
  # qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True, chain_type_kwargs=chain_type_kwargs)

  # res = qa({"query": "What is a seed lexicon?"})
  # answer, docs = res["answer"], res["source_documents"]
  # logger.info(f"Answer: {answer}")
  # logger.info(f"Docs: {docs}")

  return prompt_context