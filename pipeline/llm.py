from langchain.llms.base import LLM
from langchain.schema import Document
from typing import List, Optional

from . import config

class CustomLLM(LLM):
  from langchain.callbacks.manager import CallbackManagerForLLMRun
  from langchain.llms.base import LLM

  answer = ""
  evidence = []

  @property
  def _llm_type(self) -> str:
    return "custom"
  
  def _call(
    self,
    prompt: str,
    stop: Optional[List[str]] = None,
    run_manager: Optional[CallbackManagerForLLMRun] = None,
  ) -> str:
    import requests

    if stop is not None:
      raise ValueError("stop kwargs are not permitted.")
    answer = ""

    system_prompt = "You are a model trained on diverse datasets, you have the ability to provide insights on a wide range of topics, including machine learning."
    headers = {
      "Authorization": f"Bearer {config.PAWAN_API_KEY}",
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
      "max_tokens": 256,
      "messages": messages,
    }

    response = requests.post(config.PAWAN_API_URL, headers=headers, json=payload)
    if response.status_code != 200:
      raise Exception(f"PawanGPT ERROR: {response.json()}")
    answer = response.json()['choices'][0]['message']['content']

    self.answer = answer
    return answer
  
  # used for exporting json later
  def set_evidence(self, documents: List[Document]):
    self.evidence = [documents.page_content for documents in documents]
  
  def qasper_export_jsonl(self, question_id: str, path: str):
    import json
    
    json_data = {
      "question_id": question_id,
      "predicted_answer": self.answer,
      "predicted_evidence": self.evidence,
    }

    with open(path, 'a') as f:
      f.write(json.dumps(json_data) + '\n')

    return json.dumps(json_data)