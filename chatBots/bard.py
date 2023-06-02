from os import environ
from bardapi import Bard
from .chatGPT import revChatGPT
import json

class revBard:
  def __init__(self, session_token):
    self.chatbot = Bard(token=session_token)
    self.answer = ""

  def __init__(self):
    self.chatbot = Bard(token="XAityxgcgvle42XR_FB6RZ_MgfJjLW5dwZcoa6Z6nlHTaLnCY8TXfwfbF8HcKMMFYxaDHg.")
    self.answer = ""

  def createPrompt(self, title, abstract, arxiv_id, question):
    """Creates the prompt for Bard.

    Args:
      title: The title of the paper.
      abstract: The abstract of the paper.
      paper_id: The id of the paper.
      question: The question to Bard.

    Returns:
      The prompt for Bard.
    """
    prompt = f"""I want you to act like a machine learning professor. You will answer questions about a specific machine learning paper by following the instructions of the user.
I will give you information about a paper and a question and you will respond with an answer.
I want you to answer directly, concisely and precisely. Write in plain text without additional formatting.
I want you to answer with at most one sentence. 
Do not write long explanations, context, preamble, or introduction.
Do not write evidence or justification for your answer.
When you cannot come up with a precise answer based on the available information, or if the paper lacks sufficient evidence, write only one word: 'Unanswerable'.
When you can answer with 'yes' or 'no', write only one word 'yes' or 'no'.
When you can answer with a precise list of terms or numbers, write only the list of terms or numbers.

Use information from the following paper.
Title: {title}
Abstract: {abstract}
arXiv ID: {arxiv_id}
arXiv URL: https://arxiv.org/pdf/{arxiv_id}.pdf

My first question is: {question}"""
    return prompt

  def generate(self, user_prompt):
    """Makes api call to Bard reverse api and generate response
    populates self.answer with the response

    Args:
      user_prompt: The prompt to Bard.

    Returns:
      The response from the Bard API.
    """
    prompt = user_prompt
    try:
      response = self.chatbot.get_answer(prompt)
    except Exception as e:
      # print the error
      print(f"error: {e}")
      raise e
    # check if content is empty or exists
    bard_answer = response['content']
    
    # if bard answer conatins the phrase Google Bard encountered an error
    if "Google Bard encountered an error" in bard_answer:
      # print the error
      raise Exception(f"Bard Error: {response}")
    
    self.answer = bard_answer
    return bard_answer

  def extractAnswer(self, question):
    """Extract the actual answer terms from the bard response using chatGPT

      returns:
        answer: the answer terms extracted from the bard response
    """
    chatGPT = revChatGPT()
    system_prompt = f"""Act as a machine learning researcher. Your task is to extract a concise answer from long answer responses.
Your response should only use information from the given answer. Do not rely on your own knowledge.
You should respond with at most one sentence.
You should only respond with the extracted terms and sentence.
Do not write additional explanations, context, preamble, or introduction.
If the answer suggests the question cannot be addressed based on the available information, or if the paper lacks sufficient evidence, your response should just be one word: 'Unanswerable'. 
If the answer suggests that the question can be responded to with 'yes' or 'no, please use only one word 'yes' or 'no'. 
Similarly, if the answer can be expressed as a number, a term, or a list of terms, respond with only that specific number or term(s).
Otherwise, respond with a sentence that answers the question.
My first question answer pair is:
Question: {question}
Answer: {self.answer}
"""
    user_prompt = f"Your first task is to extract answer terms or sentence from the following long answer response:\n {self.answer}"
    self.answer = chatGPT.generate(system_prompt, user_prompt)
    return self.answer
  
  def sample(self, prompt, question_id, question):
    """Makes api call to Bard reverse api and generate response and extract answer terms

    Args:
      prompt: The prompt to Bard.
      question_id: The question id.

    Returns:
      The extracted answer.
    """
    response = self.generate(prompt)
    answer = self.extractAnswer(question)

    evidence = ["no evidence found"]
    json_obj = {
        "question_id": question_id,
        "predicted_answer": self.answer,
        "predicted_evidence": evidence
    }

    with open('bard_response.jsonl', 'a') as f:
      f.write(json.dumps(json_obj) + '\n')

    time.sleep(10)

    return self.answer