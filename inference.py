import json
from customLLM import CustomLLM, ChatBotType, TaskType
from prompts import PromptGenerator
from tqdm import tqdm
import sys
import time
  
# TODO: build out the pipeline for REALM using modal
  # familiarize with existing code
  # Step 1: transition modal to use langchain chroma vector store
  #   1a: try out add, query, and delete
  # Step 2: Run the instruct embedding on modal
  # 2a: need to store the instruct XL somehow and run on T4 GPU

# run chatGPT on the test set
# for each question, get the answer and evidence
# evaluate the answer and evidence
# print the results

TRIALS = 1000

chatbot = ChatBotType.PAWAN
# chatbot = ChatBotType.PROXY
# chatbot = ChatBotType.BARD

llm = CustomLLM(chatBot=chatbot)

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
        question = qa["question"]
        question_id = qa["question_id"]
        # run LLM inference and save sample to disk
        try:
          task = TaskType.FREEFORM

          prompt = PromptGenerator(title, key, question).freeFormQA(chatbot)
          llm(prompt)

          result_path = f"out/{chatbot.name.lower()}_{task.name.lower()}_result.jsonl"
          llm.sample(task, question_id, result_path)
        except Exception as e:
          # print the error
          print(f"question {count}: {question_id}")
          print(f"Inference error: {e}")
          continue

        count += 1
        pbar.update(1)
      # if count % 10 == 0:
      #   print(f"question answered: {count}")


