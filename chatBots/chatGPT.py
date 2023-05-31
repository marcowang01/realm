import requests
import json


API_KEY = "pk-SCfIRSxcfoewLTsUagmpHJMVFwVbPjHDrNeVJAbagnnEjzLD"
MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 100

def chat_completion(api_key, model, max_tokens, messages):
  """Makes a request to the Chat Completion (ChatGPT) API.

  Args:
    api_key: The API key for the Chat Completion (ChatGPT) API.
    model: The model to use for the completion.
    max_tokens: The maximum number of tokens to return.
    messages: The messages to complete.

  Returns:
    The response from the Chat Completion (ChatGPT) API.
  """

  headers = {
    "Authorization": "Bearer {}".format(api_key),
    "Content-Type": "application/json",
  }

  payload = {
    "model": model,
    "max_tokens": max_tokens,
    "messages": messages,
  }

  response = requests.post("https://api.pawan.krd/v1/chat/completions", headers=headers, json=payload)

  return response


def chatGPT(system_prompt, user_prompt):
  """Act as chatGPT bot. Saves output to a json file.
  
  Args:
    promppt: The promppt to chatGPT.

  Returns:
    The response from the Chat Completion (ChatGPT) API.
  """
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
  print("Ping chatGPT API...")
  response = chat_completion(API_KEY, MODEL, MAX_TOKENS, messages)
  if response.status_code == 200:
    completion = response.json()['choices'][0]['message']['content']
    json_obj = {
      "prompt": user_prompt,
      "response": completion,
    }
    try:
      with open('chatGPT_response.json', 'r') as f:
        data = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
      data = []

    data.append(json_obj)
    with open('chatGPT_response.json', 'w') as f:
      json.dump(data, f, indent=4)
      
  else:
    raise Exception(f"Error making request to chatGPT API with response {response.json()}")

  return completion


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