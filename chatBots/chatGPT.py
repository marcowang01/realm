import requests
import json

class revChatGPT:
  def __init__(self, api_key, model, max_tokens):
    self.api_key = api_key
    self.model = model
    self.max_tokens = max_tokens
    self.answer = ""

  def __init__(self):
    self.api_key = "pk-SCfIRSxcfoewLTsUagmpHJMVFwVbPjHDrNeVJAbagnnEjzLD"
    self.model = "gpt-3.5-turbo"
    self.max_tokens = 100
    self.answer = ""

  def createPropmt(self, title, abstract, arxiv_id, question):
    system_prompt = "You are a machine learning professor. You will answer questions about a specific machine learning paper by following the instructions of the user."
    user_prompt = f"""I will give you information about a paper and a question and you will respond with an answer.
I want you to answer directly, concisely and precisely.
I want you to answer with at most one sentence. 
Do not write long explanations, context, preamble, or introduction.
When you cannot come up with a precise answer based on the available information, or if the paper lacks sufficient evidence, write only one word: 'Unanswerable'.
When you can answer with 'yes' or 'no', write only one word 'yes' or 'no'.
When you can answer with a precise list of terms or numbers, write only the list of terms or numbers.

Use information and context from the following paper.
Title: {title}
Abstract: {abstract}
arXiv ID: {arxiv_id}
arXiv URL: https://arxiv.org/pdf/{arxiv_id}.pdf

My first question is: {question}"""
    return system_prompt, user_prompt

  def generate(self, system_prompt, user_prompt):
    """Makes a request to the Chat Completion (ChatGPT) API.

    Args:
      system_prompt: The system prompt to chatGPT. Used to construct message
      user_prompt: The user prompt to chatGPT. Used to construct message

    Returns:
      The response from the Chat Completion (ChatGPT) API.
    """

    headers = {
      "Authorization": "Bearer {}".format(self.api_key),
      "Content-Type": "application/json",
    }

    messages = [
      {
        "role": "system",
        "content": system_prompt
      },
      {
        "role": "user",
        "content": user_prompt
      }
    ]

    payload = {
      "model": self.model,
      "max_tokens": self.max_tokens,
      "messages": messages,
    }

    response = requests.post("https://api.pawan.krd/v1/chat/completions", headers=headers, json=payload)

    if response.status_code != 200:
      raise Exception(f"Error making request to chatGPT API with response {json.dumps(response.json(), indent=2)}")
    
    self.answer = response.json()['choices'][0]['message']['content']
    return self.answer

  def sample(self, system_prompt, user_prompt, question_id):
    """performs chatgGPT sampling, then saves to json file.
    
    Args:
      question_id: The id of the question to be answered
      system_prompt: The system prompt to chatGPT. Used to construct message
      user_prompt: The user prompt to chatGPT. Used to construct message

    Returns:
      The response from the Chat Completion (ChatGPT) API if successful
    """

    response = self.generate(system_prompt, user_prompt)

    evidence = ["no evidence found"]
    json_obj = {
      "question_id": question_id,
      "predicted_answer": response,
      "predicted_evidence": evidence,
    }

    with open('chatGPT_response.jsonl', 'a') as f:
      f.write(json.dumps(json_obj) + '\n') 

    return response



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