import json
from customLLM import CustomLLM, ChatBotType, TaskType
from prompts import PromptGenerator
from tqdm import tqdm
import sys
import time
import random


# TODO: build out the pipeline for REALM using modal
  # familiarize with existing code
  # Step 1: transition modal to use langchain chroma vector store
  #   1a: try out add, query, and delete
  # Step 2: Run the instruct embedding on modal
  # 2a: need to store the instruct XL somehow and run on T4 GPU

# TODO: build test pipeline
  # build automatic prompt for few shot learning
  # add the explanation part to it

TRIALS = 800

chatbot = ChatBotType.PAWAN
# chatbot = ChatBotType.PROXY
# chatbot = ChatBotType.BARD

llm = CustomLLM(chatBot=chatbot)

# load the test set
path = "qasper/qasper-test-v0.3.json"
dataset = json.load(open(path))
print(f"dataset size: {len(dataset)}")

# load in the dev set to generate examples
dev_path = "qasper/qasper-dev-v0.3.json"
dev_dataset = json.load(open(dev_path))
def extract_answer_evidence(answers):
  # extracted from qasper_evaluator.py
  annotation_info = answers[0]
  answer_info = annotation_info["answer"]
  res = {}
  if answer_info["unanswerable"]:
    res = {"answer": "Unanswerable", "evidence": []}
  else:
    if answer_info["extractive_spans"]:
        answer = ", ".join(answer_info["extractive_spans"])
    elif answer_info["free_form_answer"]:
        answer = answer_info["free_form_answer"]
    elif answer_info["yes_no"]:
        answer = "Yes"
    elif answer_info["yes_no"] is not None:
        answer = "No"
    else:
        raise RuntimeError(f"Annotation {answer_info['annotation_id']} does not contain an answer")
    
    evidence = [text for text in answer_info["highlighted_evidence"] if "FLOAT SELECTED" not in text]
    res = {"answer": answer, "evidence": evidence}

  # turn evidence into a string
  evidence = res["evidence"]
  if len(evidence) > 0:
    evidence = " ".join(evidence)
  else:
    evidence = "No evidence"
  res["evidence"] = evidence
  return res

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

          rand_keys = random.sample(list(dev_dataset.keys()), 2)
          answer_evidence = extract_answer_evidence(dev_dataset[rand_keys[0]]["qas"][0]["answers"])
          example1 = {
            "title": dev_dataset[rand_keys[0]]["title"],
            "arxiv_id": rand_keys[0],
            "question": dev_dataset[rand_keys[0]]["qas"][0]["question"],
            "answer": answer_evidence["answer"],
            "explanation": answer_evidence["evidence"]
          }
          answer_evidence = extract_answer_evidence(dev_dataset[rand_keys[1]]["qas"][0]["answers"])
          example2 = {
            "title": dev_dataset[rand_keys[1]]["title"],
            "arxiv_id": rand_keys[1],
            "question": dev_dataset[rand_keys[1]]["qas"][0]["question"],
            "answer": answer_evidence["answer"],
            "explanation": answer_evidence["evidence"]
          }

          # prompt = PromptGenerator(title, key, question).freeFormQA(example1, example2)
          prompt = PromptGenerator(title, key, question).freeFormQA(chatBotType=chatbot)
          llm(question)
          # print(f"\n*************\n{llm.answer}\n******************\n")
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


