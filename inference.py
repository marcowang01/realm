import json
from chatBots.chatGPT import revChatGPT
from chatBots.bard import revBard
from tqdm import tqdm
import sys
import time

# TODO: set up eval pipeline for three question types and have it run in the background maybe on liliths laptop
  # make a new directory for evaluation results
  # set up four modes for evaluation. pass new arg into the prompt creation and also sample and save to different files
    # boolean, extractive/abstractive, unanswerable, and evidence
  # run the eval loop for chatGPT (do bard for later)
    # run 1000 question on awand chatGPT
    # run with 15 seconds delay on bard and proxy GPT
  
# TODO: build out the pipeline for REALM using modal
  # 1: understand langchain
    # 1a: in corporate chroma onto langchain chain or build chain on my own
  # 2: Hit chroma on modal
    # 2a get the prompt back
  # 3: run ingestion on modal
 
  # 3: run final eval locally

# TODO: improvements
  # 1: privacy?
  # 2: UI?
  # 3: llama index? 
  # 4: create something that is accessible to the public and to our own projects

# run chatGPT on the test set
# for each question, get the answer and evidence
# evaluate the answer and evidence
# print the results

TRIALS = 400

bard = revBard()
chatGPT = revChatGPT()

USE_GPT = True


# load the test set
path = "qasper/qasper-test-v0.3.json"
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
            prompt = chatGPT.createPropmt(title, abstract, question_id, question)
            response = chatGPT.sample(prompt, question_id)
          else:
            prompt = bard.createPrompt(title, abstract, question_id, question)
            response = bard.sample(prompt, question_id, question)
        except Exception as e:
          # print the error
          print(question_id)
          print(f"inference error: {e}")
          continue

        count += 1
        pbar.update(1)
      # if count % 10 == 0:
      #   print(f"question answered: {count}")


