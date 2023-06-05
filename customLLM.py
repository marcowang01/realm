from typing import Any, List, Mapping, Optional
from enum import Enum
import requests
import json
import time
import re

from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from bardapi import Bard
from revChatGPT.V1 import Chatbot

# Session: Application → Cookies → Copy the value of __Secure-1PSID cookie.
BARD_ACCESS_TOKEN = "XAityxgcgvle42XR_FB6RZ_MgfJjLW5dwZcoa6Z6nlHTaLnCY8TXfwfbF8HcKMMFYxaDHg."
# https://chat.openai.com/api/auth/session
PROXY_ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJzdGFubGV5d2FuZzI5OTlAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsidXNlcl9pZCI6InVzZXItMGM2OVpaZ3BYUXltQ2Jiems3djA2QlVCIn0sImlzcyI6Imh0dHBzOi8vYXV0aDAub3BlbmFpLmNvbS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDExNTQ1NDgwNTA3MzcyMTk3MTE5OCIsImF1ZCI6WyJodHRwczovL2FwaS5vcGVuYWkuY29tL3YxIiwiaHR0cHM6Ly9vcGVuYWkub3BlbmFpLmF1dGgwYXBwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE2ODU0OTU1MjAsImV4cCI6MTY4NjcwNTEyMCwiYXpwIjoiVGRKSWNiZTE2V29USHROOTVueXl3aDVFNHlPbzZJdEciLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIG1vZGVsLnJlYWQgbW9kZWwucmVxdWVzdCBvcmdhbml6YXRpb24ucmVhZCBvcmdhbml6YXRpb24ud3JpdGUifQ.sHK-1IXcgMgSMLoeyt1wvqGafUlv5D0rFfjFN-DdMKyeq1ply10ouC3g6pd39yy25xnjlcmA-E98wC7uDC5yWfl8N7X_H7g4GtQQNwfquYT8ua3MvRnThhbwRNKaLeNc7MuC3Yh8KP4BaF8RwWcQziQttpMRQTgzP6I4iNq_7H4ugWSJ7sh1wnMZS6YKZVFU5tzwmWA7qgxwxeuTrdUsgZA_eRBenffsa8aAaTidD-9Gyif7UQb5vYr6f8FuIP_Fy9lMGfyloJTprYb50lkgbKmSiZvk7U6XKwwYjPAk6ylbAAy9-uvgcFoXWCo4g6YQBeGwHlj84mVJh_Mn1SXVfA"
PROXY_MODEL = "text-davinci-002-render-sha"
PROXY_URL = "http://localhost:9090/api/"

PAWAN_API_KEY = "pk-SCfIRSxcfoewLTsUagmpHJMVFwVbPjHDrNeVJAbagnnEjzLD"
PAWAN_API_URL = "https://api.pawan.krd/v1/chat/completions"
PAWAN_MODEL = "gpt-3.5-turbo"
PAWAN_MAX_TOKENS = 256

class ChatBotType(Enum):
  BARD = 1 # https://github.com/dsdanielpark/Bard-API
  PROXY = 2 # https://github.com/acheong08/ChatGPT, https://github.com/acheong08/ChatGPT-Proxy-V4
  PAWAN = 3 # https://github.com/PawanOsman/ChatGPT

class TaskType(Enum):
  FREEFORM = 1
  BOOLEAN = 2
  UNANS = 3
  EVIDENCE = 4

class CustomLLM(LLM):
  """
    Custom LLM for using a chatbot API as a language model.
    Methods:
      _call: generate a response from the model given a prompt.
      sample: generate a response from the model given a prompt.
      createPrompt: generate prompt for a given evaluation case.
  """
  chatBot: ChatBotType = ChatBotType.PAWAN
  # set up reverse api chatbot instances
  bard = Bard(token=BARD_ACCESS_TOKEN)
  proxyGPT = Chatbot(
    config={
    "access_token": PROXY_ACCESS_TOKEN,
    "model": PROXY_MODEL,
    "disable_history": True,
    "proxy": PROXY_URL
    }
  )
  answer = ""
  
  @property
  def _llm_type(self) -> str:
    return "custom"
  
  def _call(
    self,
    prompt: str,
    stop: Optional[List[str]] = None,
    run_manager: Optional[CallbackManagerForLLMRun] = None,
  ) -> str:
    """
      Generate a response from the model given a prompt.
    """
    if stop is not None:
      raise ValueError("stop kwargs are not permitted.")
    answer = ""

    if self.chatBot == ChatBotType.BARD:
      response = self.bard.get_answer(prompt)
      answer = response["content"]
      # weird response from Bard (i think when rate limited)
      if "Google Bard encountered an error" in answer:
        raise Exception(f"Bard Error: {response}")
      
    elif self.chatBot == ChatBotType.PROXY:
      # loop required since response is streamed
      for data in self.proxyGPT.ask(prompt):
        answer = data["message"]

    elif self.chatBot == ChatBotType.PAWAN:
      # system_prompt = "You are a helpful assistant."
      system_prompt = "You are a model trained on diverse datasets, you have the ability to provide insights on a wide range of topics, including machine learning."
      headers = {
        "Authorization": f"Bearer {PAWAN_API_KEY}",
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
        "model": PAWAN_MODEL,
        "max_tokens": PAWAN_MAX_TOKENS,
        "messages": messages,
      }

      response = requests.post(PAWAN_API_URL, headers=headers, json=payload)
      if response.status_code != 200:
        raise Exception(f"PawanGPT ERROR: {json.dumps(response.json(), indent=2)}")
      answer = response.json()['choices'][0]['message']['content']

    self.answer = answer
    return answer
  
  def sample(self, taskType: TaskType, question_id: str, path: str) -> List[str]:
    """
      Generate a sample for the QA task

      Args:
        prompt: The prompt to generate a sample for
        question_id: The id of the question on the QASPER dataset
        path: The path to the jsonl file save the sample to
    """
    json_data = {}
    if taskType == TaskType.FREEFORM:
      json_data = {
        "question_id": question_id,
        "predicted_answer": self.answer,
        "predicted_evidence": ["n/a"],
      }
    elif taskType == TaskType.EVIDENCE:
      
      # Find the substring between "Answer:" and "Evidence:"
      start_index = self.answer.find("Answer:")
      if start_index == -1:
          raise ValueError("Answer not found in the input string")

      start_index += len("Answer:")
      end_index = self.answer.find("Evidence:", start_index)
      if end_index == -1:
          raise ValueError("Evidence not found in the input string")

      answer_substring = self.answer[start_index:end_index].strip()

      # Find the substring after "Evidence:"
      evidence_substring = self.answer[end_index + len("Evidence:"):].strip()

      json_data = {
        "question_id": question_id,
        "predicted_answer": answer_substring,
        "predicted_evidence": [evidence_substring],
      }
    
    with open(path, "a") as f:
      f.write(json.dumps(json_data) + '\n')
      

  @property
  def _identifying_params(self) -> Mapping[str, Any]:
    """Get the identifying parameters."""
    return {"ChatBot Type": self.chatBot.name}
  
    

# testing code
if __name__ == "__main__":
  print("***************")
  print("testing Bard...")
  print("***************")
  llm = CustomLLM(chatBot=ChatBotType.BARD)
  print(llm._call("Hello, who are you and what can you do?"))
  print("***************")
  print("testing Proxy...")
  print("***************")
  llm = CustomLLM(chatBot=ChatBotType.PROXY)
  print(llm._call("Hello, who are you and what can you do?"))
  print("***************")
  print("testing Pawan...")
  print("***************")
  llm = CustomLLM(chatBot=ChatBotType.PAWAN)
  print(llm._call("Hello, who are you and what can you do?"))