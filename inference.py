import json
from chatBots.chatGPT import revChatGPT
from chatBots.bard import revBard
from tqdm import tqdm
import sys
import time


# run chatGPT on the test set
# for each question, get the answer and evidence
# evaluate the answer and evidence
# print the results

TRIALS = 400

bard = revBard()
chatGPT = revChatGPT()

USE_GPT = False


# load the test set
path = "qasper/qasper-train-v0.3.json"
dataset = json.load(open(path))
print(f"dataset size: {len(dataset)}")

# create chatGPT responses
count = 0
print("Begin answering questions...")
with tqdm(total=TRIALS, ncols=100, file=sys.stdout) as pbar:
  for key, value in dataset.items():
      paper = value
      title = paper["title"]
      abstract = paper["abstract"]
      if count >= TRIALS:
        break
      for qa in paper["qas"]:
        if count >= TRIALS:
          break
        # print(f"begin question: {count + 1}/{TRIALS}")
        question = qa["question"]
        question_id = qa["question_id"]
        try:
          if USE_GPT:
            system_prompt, user_prompt = chatGPT.createPropmt(title, abstract, question_id, question)
            response = chatGPT.sample(system_prompt, user_prompt, question_id)
          else:
            prompt = bard.createPrompt(title, abstract, question_id, question)
            response = bard.sample(prompt, question_id, question)
        except Exception as e:
          # print the error
          print(question_id)
          print(f"error: {e}")
          continue

        count += 1
        pbar.update(1)
      # if count % 10 == 0:
      #   print(f"question answered: {count}")


