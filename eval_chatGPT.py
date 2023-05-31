import json
from chatBots.chatGPT import chatGPT

# run chatGPT on the test set
# for each question, get the answer and evidence
# evaluate the answer and evidence
# print the results

TRIALS = 5

# load the test set
path = "qasper/qasper-test-v0.3.json"
dataset = json.load(open(path))

# create chatGPT responses
responses = []
count = 0
print("Being answering questions...")
for key, value in dataset.items():
    paper = value
    title = paper["title"]
    abstract = paper["abstract"]
    if count >= TRIALS:
      break
    for qa in paper["qas"]:
      if count >= TRIALS:
        break
      print(f"begin question: {count + 1}")
      question = qa["question"]
      system_prompt = "You are a model trained on diverse datasets, you have the ability to provide insights on a wide range of topics, including machine learning."
      user_prompt = prompt = prompt = f"""
Title: {title}
Abstract: {abstract}
arXiv ID: {key}

Using your knowledge up until September 2021, answer the following question related to this paper:

Question: {question}

Please answer directly and concisely without providing additional explanations or context and without any preamble or introduction. 
If the question cannot be answered based on available information or the paper doesn't provide enough evidence, respond with only the word 'Unanswerable'.
If the paper does not provide the necesary evidence or information related to the question, please respond only with the word 'Unanswerable'.
If the question can be answered using 'Yes' or 'No', please respond with only the word 'Yes' or 'No'.
If the question can be answered using a number, please respond with only the number.
If the question can be asnwered using a term or a list of terms, please respond with only the term or list of terms.
"""

      try:
        response = chatGPT(system_prompt, user_prompt)
      except Exception as e:
        # print the error
        print(e)
        continue

      count += 1
      if count % 10 == 0:
        print(f"question answered: {count}")

      




# prompt = f"""
# Title: {title}
# Evidence: {evidence}
# Based on the above evidence from the paper titled '{title}', can you please answer the following question?
# Question: {question}
# """
