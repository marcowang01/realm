import requests
import json
from revChatGPT.V1 import Chatbot
import time
class revChatGPT:
  def __init__(self, access_token, model, proxy):
    self.config = {
      "access_token": access_token,
      "model": model,
      "disable_history": True,
      "proxy": proxy
    }
    self.chatbot = Chatbot(config=self.config)

  def __init__(self):
    self.config = {
      "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJzdGFubGV5d2FuZzI5OTlAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsidXNlcl9pZCI6InVzZXItMGM2OVpaZ3BYUXltQ2Jiems3djA2QlVCIn0sImlzcyI6Imh0dHBzOi8vYXV0aDAub3BlbmFpLmNvbS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDExNTQ1NDgwNTA3MzcyMTk3MTE5OCIsImF1ZCI6WyJodHRwczovL2FwaS5vcGVuYWkuY29tL3YxIiwiaHR0cHM6Ly9vcGVuYWkub3BlbmFpLmF1dGgwYXBwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE2ODU0OTU1MjAsImV4cCI6MTY4NjcwNTEyMCwiYXpwIjoiVGRKSWNiZTE2V29USHROOTVueXl3aDVFNHlPbzZJdEciLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIG1vZGVsLnJlYWQgbW9kZWwucmVxdWVzdCBvcmdhbml6YXRpb24ucmVhZCBvcmdhbml6YXRpb24ud3JpdGUifQ.sHK-1IXcgMgSMLoeyt1wvqGafUlv5D0rFfjFN-DdMKyeq1ply10ouC3g6pd39yy25xnjlcmA-E98wC7uDC5yWfl8N7X_H7g4GtQQNwfquYT8ua3MvRnThhbwRNKaLeNc7MuC3Yh8KP4BaF8RwWcQziQttpMRQTgzP6I4iNq_7H4ugWSJ7sh1wnMZS6YKZVFU5tzwmWA7qgxwxeuTrdUsgZA_eRBenffsa8aAaTidD-9Gyif7UQb5vYr6f8FuIP_Fy9lMGfyloJTprYb50lkgbKmSiZvk7U6XKwwYjPAk6ylbAAy9-uvgcFoXWCo4g6YQBeGwHlj84mVJh_Mn1SXVfA",
      "model": "text-davinci-002-render-sha",
      "disable_history": True,
      "proxy": "http://localhost:9090/api/"
    }
    self.chatbot = Chatbot(config=self.config)

  def createPropmt(self, title, abstract, arxiv_id, question):
    user_prompt = f"""I want you to act as a machine learning expert. 
I will give you a question about a machin learning paper and you will answer it based on the contents of the paper.
Please answer using your knowledge in natural language processing and your training data.
Respond with only the answer. Do not respond with preamble, context, or introduction.
My first question is as follows:

In the paper with arxiv id {arxiv_id} and titled "{title}", {question}
"""

# Paper information:
# Title: {title}
# Abstract: {abstract}
# arXiv ID: {arxiv_id}
# arXiv URL: https://arxiv.org/pdf/{arxiv_id}.pdf

# My first question is: {question}"""

# I want you to answer directly, concisely and precisely.
# Do not respond with long explanations, context, preamble, or introduction.
# When you cannot come up with a answer based on your training data, I want you to respond with only one word: 'Unanswerable'.
# When you can answer with 'yes' or 'no', I want you to respond with only one word 'yes' or 'no'.
# When you can answer with a precise list of terms or numbers, I want you to respond with only the list of terms or numbers.


    return user_prompt

  def generate(self, user_prompt):
    """Makes a request to the Chat Completion (ChatGPT) API.

    Args:
      system_prompt: The system prompt to chatGPT. Used to construct message
      user_prompt: The user prompt to chatGPT. Used to construct message

    Returns:
      The response from the Chat Completion (ChatGPT) API.
    """

    # TODO: add error handling later
    
    # need to use for loop to loop through streamed response
    for data in self.chatbot.ask(user_prompt):
      self.answer = data["message"]

    # prevent rate limit
    time.sleep(1)

    return self.answer

  def sample(self, user_prompt, question_id):
    """performs chatgGPT sampling, then saves to json file.
    
    Args:
      question_id: The id of the question to be answered
      system_prompt: The system prompt to chatGPT. Used to construct message
      user_prompt: The user prompt to chatGPT. Used to construct message

    Returns:
      The response from the Chat Completion (ChatGPT) API if successful
    """

    self.generate(user_prompt)

    evidence = [self.answer]
    json_obj = {
      "question_id": question_id,
      "predicted_answer": self.answer,
      "predicted_evidence": evidence,
    }

    with open('chatGPT_response.jsonl', 'a') as f:
      f.write(json.dumps(json_obj) + '\n') 

    return self.answer



# if __name__ == "__main__":
#   # chatGPT("You are a machine learning scientist. You will answer questions about machine learning papers.", "What is the best way to train a neural network?")
#   messages = [
#     {
#       "role": "system",
#       "content": "You are a machine learning scientist. You will answer questions about machine learning papers."
#     },
#     {
#       "role": "user",
#       "content": "What is the best way to train a neural network?"
#     }
#   ]
#   response = chat_completion(API_KEY, MODEL, MAX_TOKENS, messages)
#   print(response.json())